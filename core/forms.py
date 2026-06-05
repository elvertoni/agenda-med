from django import forms

INPUT_CLASSES = (
    'block w-full rounded-xl border border-slate-700 bg-slate-900 '
    'px-3.5 py-2.5 text-slate-100 placeholder-slate-500 transition '
    'focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/40'
)
TEXTAREA_CLASSES = INPUT_CLASSES + ' min-h-[8rem]'
SELECT_CLASSES = INPUT_CLASSES + ' appearance-none'
CHECKBOX_CLASSES = (
    'h-4 w-4 rounded border-slate-700 bg-slate-900 '
    'text-emerald-500 focus:ring-emerald-400'
)

CHECKBOX_WIDGETS = (forms.CheckboxInput, forms.RadioSelect, forms.CheckboxSelectMultiple)


class StyledFormMixin:
    '''Apply design-system classes to every visible field widget.

    Plug this into a ModelForm/Form to avoid repeating widget attrs.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            if isinstance(widget, forms.Textarea):
                extra = TEXTAREA_CLASSES
            elif isinstance(widget, forms.Select):
                extra = SELECT_CLASSES
            elif isinstance(widget, CHECKBOX_WIDGETS):
                extra = CHECKBOX_CLASSES
            else:
                extra = INPUT_CLASSES
            widget.attrs['class'] = (existing + ' ' + extra).strip()
