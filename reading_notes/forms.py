from django import forms
from .models import ReadingNote, AffiliateLink, ReadingThemeTag


class ReadingNoteForm(forms.ModelForm):
    class Meta:
        model = ReadingNote
        fields = [
            "title",
            "author",
            "page_count",
            "status",
            "finished_at",
            "category",
            "rating",
            "is_public",
            "cover_image",
            "one_line_summary",
            "reading_purpose",
            "theme_tags",
            "impression_during",
            "impression_after",
            "comparison_notes",
            "theme_notes",
            "unwritten_notes",
            "era_common_notes",
            "universal_theme_notes",
        ]
        widgets = {
            "theme_tags": forms.CheckboxSelectMultiple(),
            "finished_at": forms.DateInput(attrs={"type": "date"}),
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "step": 1}),
            "page_count": forms.NumberInput(attrs={"min": 1, "step": 1}),
        }
        labels = {
            "theme_tags": "タグ",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["theme_tags"].queryset = ReadingThemeTag.objects.filter(owner=user)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("rows", 3)

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        finished_at = cleaned.get("finished_at")
        if status == ReadingNote.Status.FINISHED and not finished_at:
            self.add_error("finished_at", "読了のときは読了日を入力してください。")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.status != ReadingNote.Status.FINISHED:
            instance.finished_at = None
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class AffiliateLinkForm(forms.ModelForm):
    class Meta:
        model = AffiliateLink
        fields = ["kind", "url"]
        widgets = {
            "kind": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "kind":
                field.widget.attrs.setdefault("class", "form-control")

        # make URL label fixed per kind
        kind = self.initial.get("kind") or getattr(self.instance, "kind", "")
        if kind == AffiliateLink.Kind.AMAZON:
            self.fields["url"].label = "Amazon\u30ea\u30f3\u30af"
        elif kind == AffiliateLink.Kind.RAKUTEN:
            self.fields["url"].label = "\u697d\u5929\u30ea\u30f3\u30af"

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("kind")
        url = cleaned.get("url")
        if url and not kind:
            raise forms.ValidationError("\u30ea\u30f3\u30af\u7a2e\u5225\u304c\u4e0d\u6b63\u3067\u3059\u3002")
        return cleaned

class ReadingThemeTagForm(forms.ModelForm):
    class Meta:
        model = ReadingThemeTag
        fields = ["name", "knowledge_url"]
        labels = {
            "name": "\u30bf\u30b0\u540d",
            "knowledge_url": "Knowledge Base URL",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "knowledge_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if self.user:
            existing = ReadingThemeTag.objects.filter(owner=self.user, name=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("\u540c\u3058\u30bf\u30b0\u540d\u304c\u3059\u3067\u306b\u3042\u308a\u307e\u3059\u3002")
        return name
