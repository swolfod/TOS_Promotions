from . import djangoUtils


class EntryTimeStamp:
    field = "timeStamp"
    relatedFields = []
    model = None

    @classmethod
    def update(cls, entry, changedFields=None):
        if entry is None or changedFields is not None and len(changedFields) == 0:
            return

        if None in [changedFields, cls.relatedFields] or cls.field in changedFields or \
                set(changedFields) & set(cls.relatedFields):
            entries = entry if isinstance(entry, list) else [entry]
            if not entries:
                return

            entryIds = [item.pk for item in entries] if isinstance(entries[0], cls.model) else entries
            cls.model.objects.filter(pk__in=entryIds).update(**{cls.field: djangoUtils.getCurrentTimeStamp()})
