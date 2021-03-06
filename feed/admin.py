from django.contrib import admin
from .models import FeedLike, FeedView, FeedConfig, FeedEntry, FeedEntryLike, FeedEntryView
from django import forms
from django.db.models import Count
from django.core.management import call_command
from django.db.models import Prefetch


def check_feed_action(modeladmin, request, queryset):
    for modelinstance in queryset:
        modelinstance.check_feeds(force=True)


check_feed_action.short_description = 'Check for new feeds'


class FeedConfigForm(forms.ModelForm):
    url = forms.URLField(help_text='Enter URL with authentication parameter',
                         widget=forms.TextInput(attrs={'autocomplete': 'off', }))

    def save(self, commit=True):
        feed_config = super(FeedConfigForm, self).save(commit)
        feed_config.url = self.cleaned_data['url']
        feed_config.save()
        call_command('feed_cron')
        return feed_config

    class Meta:
        model = FeedConfig
        fields = ['url', 'check_frequency']


class FeedConfigAdmin(admin.ModelAdmin):
    list_display = ['title', 'link', 'updated', 'last_checked', 'check_frequency', 'etag', 'entry_count']
    exclude = ['url']
    form = FeedConfigForm
    actions = [check_feed_action]

    def get_queryset(self, request):
        return FeedConfig.objects.all().annotate(entry_count=Count('entries', distinct=True))

    def entry_count(self, ins):
        return ins.entry_count


class FeedEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'feed_config', 'title', 'updated', 'published', 'total_likes', 'total_views']

    def get_queryset(self, request):
        return FeedEntry.objects.all().prefetch_related(
            Prefetch('likes', FeedEntryLike.objects.all())
        ).prefetch_related(Prefetch('views', FeedEntryView.objects.all()))

    def total_likes(self, ins):
        return ins.likes.count()

    def total_views(self, ins):
        return ins.views.count()


class FeedAdmin(admin.ModelAdmin):
    list_display = ['guid', 'user']


admin.site.register(FeedConfig, FeedConfigAdmin)
admin.site.register(FeedEntry, FeedEntryAdmin)
admin.site.register(FeedLike, FeedAdmin)
admin.site.register(FeedView, FeedAdmin)
