(() => {
    "use strict";

    const app = document.getElementById("room-draw");
    if (!app) return;

    const element = (id) => document.getElementById(id);
    const setupView = element("setup-view");
    const presentationView = element("presentation-view");
    const form = element("roster-form");
    const roster = element("roster");
    const prepareButton = element("prepare-button");
    const drawButton = element("draw-button");
    const revealButton = element("reveal-button");
    const copyButton = element("copy-button");
    const board = element("room-board");
    const drawStatus = element("draw-status");
    const presentationTitle = element("presentation-title");
    const manualCopyPanel = element("manual-copy-panel");
    const copyText = element("copy-text");
    const copyStatus = element("copy-status");
    const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
    const navigationLinks = app.querySelectorAll("[data-navigation-lock]");
    const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const participantLimit = 20;
    const requestTimeout = 15000;
    const timers = new Set();
    const animationTimers = new Set();
    const state = { busy: false, participants: [], result: null, revealedCount: 0, operation: 0 };
    let activeRequest = null;
    let finishAnimation = null;

    const cards = Array.from(board.querySelectorAll(".room-card"), (card) => {
        const list = card.querySelector(".room-members");
        const capacity = Number(card.dataset.capacity);
        const slots = Array.from({ length: capacity }, () => document.createElement("li"));
        list.replaceChildren(...slots);
        return {
            node: card,
            number: card.dataset.roomNumber,
            capacity,
            name: card.querySelector(".room-name"),
            list,
            slots,
            status: card.querySelector(".room-state"),
        };
    });

    class DisplayError extends Error {
        constructor(message, reload = false) {
            super(message);
            this.reload = reload;
        }
    }

    function later(callback, delay) {
        const timer = window.setTimeout(() => {
            timers.delete(timer);
            callback();
        }, delay);
        timers.add(timer);
        return timer;
    }

    function cancelTimer(timer) {
        window.clearTimeout(timer);
        timers.delete(timer);
    }

    function setBusy(busy) {
        state.busy = busy;
        app.querySelectorAll("button").forEach((button) => { button.disabled = busy; });
        const pending = hasUnrevealedRooms();
        drawButton.disabled = busy || pending;
        revealButton.disabled = busy || !pending;
        copyButton.disabled = busy || !state.result || pending;
        element("edit-button").disabled = busy || pending;
        roster.readOnly = busy;
        form.setAttribute("aria-busy", String(busy));
        navigationLinks.forEach((link) => {
            if (busy) {
                link.setAttribute("aria-disabled", "true");
                link.setAttribute("tabindex", "-1");
            } else {
                link.removeAttribute("aria-disabled");
                link.removeAttribute("tabindex");
            }
        });
        readRoster();
    }

    function clearError() {
        element("error-panel").hidden = true;
        element("error-message").textContent = "";
        element("reload-link").hidden = true;
    }

    function showError(error) {
        element("error-message").textContent = error instanceof DisplayError
            ? error.message
            : "通信に失敗しました。接続を確認して、もう一度お試しください。";
        element("reload-link").hidden = !(error instanceof DisplayError && error.reload);
        element("error-panel").hidden = false;
    }

    function resetCopy() {
        copyStatus.textContent = "";
        copyText.value = "";
        manualCopyPanel.hidden = true;
    }

    function readRoster(showCountError = false) {
        const names = roster.value.split(/\r\n?|\n/).map((name) => name.trim()).filter(Boolean);
        const seen = new Set();
        const duplicates = new Set();
        names.forEach((name) => {
            const key = name.normalize("NFKC").toLowerCase();
            if (seen.has(key)) duplicates.add(name);
            seen.add(key);
        });
        const valid = names.length === participantLimit && duplicates.size === 0;
        prepareButton.disabled = state.busy || !valid;
        const invalid = duplicates.size > 0 || names.length > participantLimit || (showCountError && !valid);
        let message;
        if (duplicates.size) {
            message = `名前が重複しています：${Array.from(duplicates).join("、")}。同姓同名の場合は区別できる表記にしてください。`;
        } else if (names.length < participantLimit) {
            message = names.length === 0
                ? "20人の名前を入力してください。"
                : `あと${participantLimit - names.length}人入力してください。`;
        } else if (names.length > participantLimit) {
            message = `${names.length - participantLimit}人多く入力されています。20人にしてください。`;
        } else {
            message = "20人の名前がそろいました。抽選画面に進めます。";
        }
        element("participant-count").textContent = String(names.length);
        element("roster-count").classList.toggle("is-ready", valid);
        element("roster-validation").textContent = message;
        element("roster-validation").classList.toggle("is-error", invalid);
        roster.setAttribute("aria-invalid", String(invalid));
        return { names, valid };
    }

    async function post(url, names) {
        const controller = new AbortController();
        activeRequest = controller;
        let timedOut = false;
        const timer = later(() => {
            timedOut = true;
            controller.abort();
        }, requestTimeout);
        try {
            const response = await fetch(url, {
                method: "POST",
                mode: "same-origin",
                credentials: "same-origin",
                cache: "no-store",
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "X-CSRFToken": csrfToken,
                },
                body: new URLSearchParams({ roster: names.join("\n") }).toString(),
                signal: controller.signal,
            });
            if (response.redirected || response.status === 401) {
                throw new DisplayError("ログイン状態を確認できませんでした。名簿を控えてから、このページを開き直してください。", true);
            }
            if (response.status === 403) {
                throw new DisplayError("ページの有効期限が切れた可能性があります。名簿を控えてから、このページを開き直してください。", true);
            }
            if (!(response.headers.get("Content-Type") || "").toLowerCase().includes("application/json")) {
                throw new DisplayError("サーバーから正しい応答を受け取れませんでした。時間をおいて、もう一度お試しください。");
            }
            let data;
            try {
                data = await response.json();
            } catch (error) {
                if (controller.signal.aborted) throw error;
                throw new DisplayError("応答を読み取れませんでした。もう一度お試しください。");
            }
            if (!response.ok) {
                const message = [400, 503].includes(response.status) && typeof data?.error === "string" && data.error.trim()
                    ? data.error
                    : "処理できませんでした。時間をおいて、もう一度お試しください。";
                throw new DisplayError(message);
            }
            return data;
        } catch (error) {
            if (timedOut) throw new DisplayError("通信がタイムアウトしました。接続を確認して、もう一度お試しください。");
            throw error;
        } finally {
            cancelTimer(timer);
            if (activeRequest === controller) activeRequest = null;
        }
    }

    function validateParticipants(data, expected) {
        const names = data?.participants;
        if (!Array.isArray(names) || names.length !== participantLimit
            || names.some((name) => typeof name !== "string" || !name.trim())
            || new Set(names).size !== participantLimit
            || names.some((name) => !expected.includes(name))) {
            throw new DisplayError("参加者を確認できませんでした。もう一度お試しください。");
        }
        return names.slice();
    }

    function validateRooms(data) {
        const invalidResponse = () => new DisplayError("抽選結果を確認できませんでした。もう一度お試しください。");
        if (!Array.isArray(data?.rooms) || data.rooms.length !== cards.length) throw invalidResponse();
        const remaining = new Set(state.participants);
        // Validate the complete result before replacing anything already on screen.
        const rooms = cards.map((card) => {
            const matches = data.rooms.filter((room) => room && String(room.number) === card.number);
            if (matches.length !== 1) throw invalidResponse();
            const room = matches[0];
            if (room.capacity !== card.capacity || typeof room.name !== "string" || !room.name.trim()
                || !Array.isArray(room.members) || room.members.length !== card.capacity) throw invalidResponse();
            room.members.forEach((name) => {
                if (typeof name !== "string" || !remaining.delete(name)) throw invalidResponse();
            });
            return { number: room.number, name: room.name, capacity: room.capacity, members: room.members.slice() };
        });
        if (remaining.size) throw invalidResponse();
        return rooms;
    }

    function resetBoard(label = "待機中") {
        cards.forEach((card) => {
            card.node.classList.remove("is-shuffling", "is-revealed", "is-complete");
            card.list.setAttribute("aria-hidden", "true");
            card.status.textContent = label === "待機中" ? "抽選前" : label;
            card.slots.forEach((slot) => {
                slot.textContent = label;
                slot.className = "is-placeholder";
            });
        });
        board.setAttribute("aria-busy", "false");
    }

    function revealRoom(room, index, animate = false) {
        const card = cards[index];
        card.name.textContent = room.name;
        card.list.setAttribute("aria-label", `${room.name}のメンバー`);
        card.list.removeAttribute("aria-hidden");
        card.slots.forEach((slot, slotIndex) => {
            slot.textContent = room.members[slotIndex];
            slot.className = "";
        });
        card.node.classList.remove("is-shuffling");
        card.node.classList.add("is-complete");
        card.node.classList.toggle("is-revealed", animate);
        card.status.textContent = "確定";
    }

    function hasUnrevealedRooms() {
        return Boolean(state.result && state.revealedCount < state.result.length);
    }

    function updatePresentation() {
        const pending = hasUnrevealedRooms();
        board.setAttribute("aria-busy", "false");
        drawButton.hidden = pending;
        drawButton.textContent = state.result ? "全員を再抽選" : "抽選開始";
        revealButton.hidden = !pending;
        copyButton.hidden = !state.result || pending;
        if (pending) {
            const nextRoom = state.result[state.revealedCount];
            revealButton.textContent = `${nextRoom.name}を発表`;
            presentationTitle.textContent = "部屋割りの発表";
            drawStatus.textContent = `${state.revealedCount} / ${state.result.length}部屋を発表済みです。「${nextRoom.name}を発表」を押してください。`;
        } else {
            presentationTitle.textContent = state.result ? "部屋割りの結果" : "部屋割り抽選";
            drawStatus.textContent = state.result
                ? "全員の部屋割りが決まりました。"
                : "準備ができました。「抽選開始」を押してください。";
        }
    }

    function restorePresentation() {
        resetBoard(state.result ? "発表待ち" : "待機中");
        // Restore only rooms the operator has already announced, including on page return.
        if (state.result) {
            state.result.slice(0, state.revealedCount).forEach((room, index) => revealRoom(room, index));
        }
        updatePresentation();
    }

    function scheduleAnimation(callback, delay) {
        const timer = later(() => {
            animationTimers.delete(timer);
            callback();
        }, delay);
        animationTimers.add(timer);
        return timer;
    }

    function animateShuffle() {
        restorePresentation();
        if (motionPreference.matches || document.hidden) {
            return Promise.resolve();
        }
        board.setAttribute("aria-busy", "true");
        drawStatus.textContent = "抽選中です。演出が終わったら、ボタンで1部屋ずつ発表できます。";
        return new Promise((resolve) => {
            let shuffling = true;
            finishAnimation = () => {
                shuffling = false;
                animationTimers.forEach(cancelTimer);
                animationTimers.clear();
                finishAnimation = null;
                restorePresentation();
                resolve();
            };
            // These shuffled names are visual placeholders, never the draw result.
            const shuffleFrame = () => {
                if (!shuffling) return;
                const names = state.participants.slice();
                for (let i = names.length - 1; i > 0; i -= 1) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [names[i], names[j]] = [names[j], names[i]];
                }
                let nextName = 0;
                cards.forEach((card) => {
                    card.node.classList.add("is-shuffling");
                    card.status.textContent = "抽選中";
                    card.slots.forEach((slot) => {
                        slot.className = "";
                        slot.textContent = names[nextName++];
                    });
                });
                scheduleAnimation(shuffleFrame, 120);
            };
            shuffleFrame();
            scheduleAnimation(() => { if (finishAnimation) finishAnimation(); }, 2000);
        });
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (state.busy) return;
        clearError();
        const { names, valid } = readRoster(true);
        if (!valid) {
            roster.focus();
            return;
        }
        const operation = ++state.operation;
        setBusy(true);
        prepareButton.textContent = "名簿を確認中";
        try {
            const data = await post(app.dataset.prepareUrl, names);
            if (operation !== state.operation) return;
            state.participants = validateParticipants(data, names);
            state.result = null;
            state.revealedCount = 0;
            roster.value = state.participants.join("\n");
            readRoster();
            restorePresentation();
            resetCopy();
            setupView.hidden = true;
            presentationView.hidden = false;
            presentationTitle.focus();
        } catch (error) {
            if (operation === state.operation) showError(error);
        } finally {
            if (operation === state.operation) {
                prepareButton.textContent = "抽選画面へ";
                setBusy(false);
            }
        }
    });

    roster.addEventListener("input", () => {
        clearError();
        readRoster();
    });

    element("edit-button").addEventListener("click", () => {
        if (state.busy || hasUnrevealedRooms()) return;
        clearError();
        resetCopy();
        presentationView.hidden = true;
        setupView.hidden = false;
        readRoster();
        roster.focus();
    });

    drawButton.addEventListener("click", async () => {
        if (state.busy || !state.participants.length || hasUnrevealedRooms()) return;
        const operation = ++state.operation;
        setBusy(true);
        clearError();
        resetCopy();
        drawButton.textContent = "抽選結果を取得中";
        drawStatus.textContent = state.result
            ? "再抽選の結果を取得しています。前回の結果はそのまま表示しています。"
            : "抽選結果を取得しています。";
        try {
            const data = await post(app.dataset.drawUrl, state.participants);
            if (operation !== state.operation) return;
            const rooms = validateRooms(data);
            state.result = rooms;
            state.revealedCount = 0;
            await animateShuffle();
        } catch (error) {
            if (operation !== state.operation) return;
            showError(error);
            drawStatus.textContent = state.result
                ? "再抽選できませんでした。前回の結果を表示しています。"
                : "抽選できませんでした。「抽選開始」からもう一度お試しください。";
        } finally {
            if (operation === state.operation) {
                drawButton.textContent = state.result ? "全員を再抽選" : "抽選開始";
                setBusy(false);
                if (hasUnrevealedRooms() && !document.hidden) revealButton.focus({ preventScroll: true });
            }
        }
    });

    revealButton.addEventListener("click", () => {
        if (state.busy || !hasUnrevealedRooms()) return;
        const index = state.revealedCount;
        revealRoom(state.result[index], index, !motionPreference.matches);
        state.revealedCount += 1;
        updatePresentation();
        setBusy(false);
        if (!hasUnrevealedRooms()) copyButton.focus({ preventScroll: true });
    });

    function resultText() {
        return "部屋割り\n\n" + state.result.map((room) =>
            `${room.name}（${room.capacity}人）\n${room.members.map((name) => `・${name}`).join("\n")}`
        ).join("\n\n");
    }

    async function tryClipboard(text) {
        let timer;
        try {
            if (!navigator.clipboard?.writeText) return false;
            return await Promise.race([
                navigator.clipboard.writeText(text).then(() => true, () => false),
                new Promise((resolve) => { timer = later(() => resolve(false), 4000); }),
            ]);
        } catch (_) {
            return false;
        } finally {
            cancelTimer(timer);
        }
    }

    function tryLegacyCopy(text) {
        const buffer = document.createElement("textarea");
        const previousFocus = document.activeElement;
        buffer.className = "clipboard-buffer";
        buffer.value = text;
        buffer.readOnly = true;
        buffer.setAttribute("aria-label", "コピー用の部屋割り結果");
        document.body.appendChild(buffer);
        try {
            buffer.focus({ preventScroll: true });
            buffer.select();
            buffer.setSelectionRange(0, buffer.value.length);
            return Boolean(document.execCommand("copy"));
        } catch (_) {
            return false;
        } finally {
            buffer.remove();
            if (previousFocus && !previousFocus.disabled) previousFocus.focus({ preventScroll: true });
        }
    }

    function selectCopyText() {
        copyText.focus({ preventScroll: true });
        copyText.select();
        copyText.setSelectionRange(0, copyText.value.length);
    }

    copyButton.addEventListener("click", async () => {
        if (state.busy || !state.result || hasUnrevealedRooms()) return;
        const operation = ++state.operation;
        const text = resultText();
        setBusy(true);
        resetCopy();
        copyStatus.textContent = "コピーしています。";
        try {
            const copied = await tryClipboard(text);
            if (operation !== state.operation) return;
            if (copied || tryLegacyCopy(text)) {
                copyStatus.textContent = "全員の部屋割りをコピーしました。";
            } else {
                copyText.value = text;
                manualCopyPanel.hidden = false;
                copyStatus.textContent = "下のテキストからコピーしてください。";
                manualCopyPanel.scrollIntoView({ block: "nearest", behavior: "auto" });
                selectCopyText();
            }
        } finally {
            if (operation === state.operation) {
                setBusy(false);
                if (manualCopyPanel.hidden) copyButton.focus({ preventScroll: true });
            }
        }
    });

    element("select-copy-button").addEventListener("click", () => {
        if (!state.busy) selectCopyText();
    });

    navigationLinks.forEach((link) => {
        const preventBusyNavigation = (event) => { if (state.busy) event.preventDefault(); };
        link.addEventListener("click", preventBusyNavigation);
        link.addEventListener("auxclick", preventBusyNavigation);
    });

    document.addEventListener("visibilitychange", () => {
        if (document.hidden && finishAnimation) finishAnimation();
    });
    motionPreference.addEventListener("change", () => {
        if (motionPreference.matches && finishAnimation) finishAnimation();
    });
    window.addEventListener("pagehide", () => {
        // Invalidate in-flight callbacks, including when returning from the back-forward cache.
        state.operation += 1;
        if (activeRequest) activeRequest.abort();
        if (finishAnimation) finishAnimation();
        timers.forEach((timer) => window.clearTimeout(timer));
        timers.clear();
        animationTimers.clear();
        prepareButton.textContent = "抽選画面へ";
        restorePresentation();
        copyStatus.textContent = "";
        setBusy(false);
    });
    window.addEventListener("pageshow", () => { readRoster(); });

    resetBoard();
    readRoster();
    setBusy(false);
})();
