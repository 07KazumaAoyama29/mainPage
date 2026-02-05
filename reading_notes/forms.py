from django import forms
from .models import ReadingNote, AffiliateLink


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
            "impression_during",
            "impression_after",
            "comparison_notes",
            "theme_notes",
            "unwritten_notes",
            "era_common_notes",
            "universal_theme_notes",
        ]
        widgets = {
            "finished_at": forms.DateInput(attrs={"type": "date"}),
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "step": 1}),
            "page_count": forms.NumberInput(attrs={"min": 1, "step": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
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
        fields = ["label", "url", "sort_order"]
        widgets = {
            "sort_order": forms.NumberInput(attrs={"min": 0, "step": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
