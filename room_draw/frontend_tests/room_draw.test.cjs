const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const script = fs.readFileSync(path.join(root, "static/room_draw/room_draw.js"), "utf8");
const template = fs.readFileSync(path.join(root, "templates/room_draw/index.html"), "utf8");

// A small DOM/timer double exercises the shipped event handlers without a browser dependency.
class Element {
    constructor() {
        this.listeners = {};
        this.attributes = new Map();
        this.children = [];
        this.dataset = {};
        this.value = "";
        this.textContent = "";
        this.hidden = false;
        const classes = new Set();
        this.classList = {
            add: (...names) => names.forEach((name) => classes.add(name)),
            remove: (...names) => names.forEach((name) => classes.delete(name)),
            contains: (name) => classes.has(name),
            toggle: (name, force) => force ? classes.add(name) : classes.delete(name),
        };
    }
    addEventListener(type, callback) { (this.listeners[type] ??= []).push(callback); }
    emit(type) {
        return Promise.all((this.listeners[type] || []).map((callback) => callback({ preventDefault() {} })));
    }
    setAttribute(name, value) { this.attributes.set(name, value); }
    removeAttribute(name) { this.attributes.delete(name); }
    replaceChildren(...children) { this.children = children; }
    focus() {}
    select() {}
    setSelectionRange() {}
    scrollIntoView() {}
}

function createApp({ reducedMotion = false, hidden = false } = {}) {
    const elements = Object.fromEntries([...template.matchAll(/id="([^"]+)"/g)].map((match) => [match[1], new Element()]));
    const buttons = [...template.matchAll(/<button[^>]*id="([^"]+)"/g)].map((match) => elements[match[1]]);
    const participants = Array.from({ length: 20 }, (_, index) => `person-${index + 1}`);
    let offset = 0;
    const rooms = [4, 3, 3, 5, 5].map((capacity, index) => {
        const members = participants.slice(offset, offset + capacity);
        offset += capacity;
        return { number: index + 1, name: `Room ${index + 1}`, capacity, members };
    });
    const cards = rooms.map((room) => {
        const card = new Element();
        card.dataset = { capacity: String(room.capacity), roomNumber: String(room.number) };
        card.parts = Object.fromEntries([".room-members", ".room-name", ".room-state"].map((name) => [name, new Element()]));
        card.querySelector = (selector) => card.parts[selector];
        return card;
    });
    elements["room-board"].querySelectorAll = () => cards;
    elements["roster-form"].querySelector = () => ({ value: "csrf-test-token" });
    elements["room-draw"].dataset = { prepareUrl: "/prepare/", drawUrl: "/draw/" };
    elements["room-draw"].querySelectorAll = (selector) => selector === "button" ? buttons : [];
    const document = new Element();
    document.hidden = hidden;
    document.getElementById = (id) => elements[id];
    document.createElement = () => new Element();
    const preference = new Element();
    preference.matches = reducedMotion;
    const window = new Element();
    const timers = new Map();
    let now = 0;
    let timerId = 0;
    window.setTimeout = (callback, delay) => {
        const id = ++timerId;
        timers.set(id, { callback, due: now + delay });
        return id;
    };
    window.clearTimeout = (id) => timers.delete(id);
    window.matchMedia = () => preference;
    const requests = [];
    const copied = [];
    const failures = [];
    const fetch = async (url) => {
        requests.push(url);
        if (failures.length) throw failures.shift();
        return {
            ok: true,
            status: 200,
            redirected: false,
            headers: { get: () => "application/json" },
            json: async () => url === "/prepare/" ? { participants } : { rooms },
        };
    };
    vm.runInNewContext(script, {
        document, window, fetch, AbortController, URLSearchParams,
        navigator: { clipboard: { writeText: async (text) => { copied.push(text); } } },
    });
    return {
        elements, cards, document, window, preference, requests, copied, failures, participants,
        revealed: () => cards.filter((card) => card.classList.contains("is-complete")).length,
        async prepare() {
            elements.roster.value = participants.join("\n");
            await elements.roster.emit("input");
            await elements["roster-form"].emit("submit");
        },
        advance(ms) {
            const end = now + ms;
            while (true) {
                const next = [...timers].filter(([, timer]) => timer.due <= end)
                    .sort((a, b) => a[1].due - b[1].due || a[0] - b[0])[0];
                if (!next) break;
                timers.delete(next[0]);
                now = next[1].due;
                next[1].callback();
            }
            now = end;
        },
    };
}

const flushPromises = () => new Promise(setImmediate);

test("shuffle waits for clicks; each click reveals exactly one room without another draw", async () => {
    const app = createApp();
    await app.prepare();
    const drawing = app.elements["draw-button"].emit("click");
    await flushPromises();
    assert.equal(app.elements["reveal-button"].disabled, true);
    await app.elements["reveal-button"].emit("click");
    app.advance(2000);
    await drawing;
    app.advance(60000);
    assert.equal(app.revealed(), 0);
    assert.equal(app.elements["draw-button"].hidden, true);
    assert.equal(app.elements["copy-button"].hidden, true);
    assert.equal(app.elements["reveal-button"].disabled, false);
    await app.elements["copy-button"].emit("click");
    await app.elements["draw-button"].emit("click");
    assert.equal(app.copied.length, 0);
    for (let count = 1; count <= 5; count += 1) {
        await app.elements["reveal-button"].emit("click");
        app.advance(60000);
        assert.equal(app.revealed(), count);
        assert.equal(app.elements["copy-button"].hidden, count < 5);
    }
    assert.equal(app.requests.filter((url) => url === "/draw/").length, 1);
    assert.equal(app.elements["draw-button"].hidden, false);
    assert.equal(app.elements["reveal-button"].hidden, true);
    await app.elements["copy-button"].emit("click");
    assert.equal(app.copied.length, 1);
    for (const name of app.participants) assert.ok(app.copied[0].includes(name));
});

for (const options of [{ reducedMotion: true }, { hidden: true }]) {
    test(`skipping the shuffle still requires manual reveal: ${JSON.stringify(options)}`, async () => {
        const app = createApp(options);
        await app.prepare();
        await app.elements["draw-button"].emit("click");
        app.advance(60000);
        assert.equal(app.revealed(), 0);
        await app.elements["reveal-button"].emit("click");
        assert.equal(app.revealed(), 1);
    });
}

test("leaving during shuffle or partial presentation never reveals the remaining rooms", async () => {
    const app = createApp();
    await app.prepare();
    const drawing = app.elements["draw-button"].emit("click");
    await flushPromises();
    app.document.hidden = true;
    await app.document.emit("visibilitychange");
    await drawing;
    assert.equal(app.revealed(), 0);
    app.document.hidden = false;
    await app.elements["reveal-button"].emit("click");
    await app.elements["reveal-button"].emit("click");
    await app.window.emit("pagehide");
    await app.window.emit("pageshow");
    app.advance(60000);
    assert.equal(app.revealed(), 2);
    assert.equal(app.elements["copy-button"].hidden, true);
    assert.equal(app.elements["reveal-button"].disabled, false);
});

test("redraw failures preserve the previous result; a successful redraw resets revelation", async () => {
    const app = createApp({ reducedMotion: true });
    await app.prepare();
    await app.elements["draw-button"].emit("click");
    for (let i = 0; i < 5; i += 1) await app.elements["reveal-button"].emit("click");
    app.failures.push(new Error("offline"));
    await app.elements["draw-button"].emit("click");
    assert.equal(app.revealed(), 5);
    assert.equal(app.elements["copy-button"].hidden, false);
    await app.elements["draw-button"].emit("click");
    assert.equal(app.revealed(), 0);
    assert.equal(app.elements["copy-button"].hidden, true);
    assert.equal(app.elements["reveal-button"].hidden, false);
});
