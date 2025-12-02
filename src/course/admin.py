from django.contrib import admin
from .models import Learn


@admin.register(Learn)
class LearnAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'youtube_id',
                    'duration', 'view_count', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('slug', 'youtube_id', 'thumbnail_url', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'youtube_url', 'duration', 'view_count')
        }),
        ('Auto-Generated Info', {
            'fields': ('slug', 'youtube_id', 'thumbnail_url', 'created_at'),
        }),
    )


# from .models import Vote
# from .models import Payment
# from .models import UserProgress
# from .models import CourseEnrollment
# from django.contrib import admin
# from .models import Course, Module, Lesson, Question, Option, UserProgress, Review


# class ModuleInline(admin.TabularInline):
#     model = Module
#     extra = 1
#     fields = ['title', 'description', 'order']


# class LessonInline(admin.TabularInline):
#     model = Lesson
#     extra = 1
#     fields = ['title', 'content', 'order', 'video_url']


# class QuestionInline(admin.TabularInline):
#     model = Question
#     extra = 1
#     fields = ['text', 'order']


# @admin.register(Lesson)
# class LessonAdmin(admin.ModelAdmin):
#     list_display = ['title', 'module', 'order']
#     list_filter = ['module__course', 'module']
#     search_fields = ['title', 'module__title']
#     inlines = [QuestionInline]
#     ordering = ['module', 'order']


# class OptionInline(admin.TabularInline):
#     model = Option
#     extra = 1
#     fields = ['text', 'is_correct']


# @admin.register(Course)
# class CourseAdmin(admin.ModelAdmin):
#     list_display = ['title', 'created_at', 'updated_at']
#     search_fields = ['title']
#     inlines = [ModuleInline]
#     ordering = ['title']


# @admin.register(Module)
# class ModuleAdmin(admin.ModelAdmin):
#     list_display = ['title', 'course', 'order']
#     list_filter = ['course']
#     search_fields = ['title', 'course__title']
#     inlines = [LessonInline]
#     ordering = ['course', 'order']


# @admin.register(Question)
# class QuestionAdmin(admin.ModelAdmin):
#     list_display = ['text', 'lesson', 'order']
#     # Filter by course and module
#     list_filter = ['lesson__module__course', 'lesson__module']
#     search_fields = ['text', 'lesson__title', 'lesson__module__title']
#     ordering = ['lesson', 'order']


# @admin.register(Option)
# class OptionAdmin(admin.ModelAdmin):
#     list_display = ['text', 'question', 'is_correct']
#     list_filter = ['question__lesson__module__course',
#                    'question__lesson__module', 'is_correct']
#     search_fields = ['text', 'question__text', 'question__lesson__title']
#     ordering = ['question__lesson', 'question']


# @admin.register(CourseEnrollment)
# class CourseEnrollmentAdmin(admin.ModelAdmin):
#     list_display = ('user', 'course', 'enrolled_at',
#                     'is_active', 'completed', 'progress_percentage')
#     list_filter = ('is_active', 'completed', 'course')
#     search_fields = ('user__username', 'course__title')
#     readonly_fields = ('enrolled_at', 'progress_percentage')

#     def progress_percentage(self, obj):
#         return f"{obj.progress_percentage}%"
#     progress_percentage.short_description = 'Progress'


# @admin.register(UserProgress)
# class UserProgressAdmin(admin.ModelAdmin):
#     list_display = ('user', 'module', 'score', 'total',
#                     'passed', 'date_completed')
#     list_filter = ('passed', 'module__course')
#     search_fields = ('user__username', 'module__title')
#     readonly_fields = ('date_completed',)


# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ('course', 'rating', 'comment', 'created_at', 'updated_at')
#     list_filter = ('course', 'rating', 'created_at')
#     search_fields = ('course__title', 'comment')
#     date_hierarchy = 'created_at'


# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('user', 'course', 'amount', 'currency',
#                     'status', 'transaction_id', 'created_at')
#     list_filter = ('status', 'currency', 'created_at')
#     search_fields = ('user__email', 'user__username',
#                      'course__title', 'transaction_id')
#     ordering = ('-created_at',)
#     readonly_fields = ('transaction_id', 'created_at', 'updated_at')

#     fieldsets = (
#         ("Payment Details", {
#             "fields": ("user", "course", "amount", "currency", "payment_method", "status")
#         }),
#         ("Transaction Info", {
#             "fields": ("transaction_id", "created_at", "updated_at"),
#             "classes": ("collapse",),
#         }),
#     )


# class VoteAdmin(admin.ModelAdmin):
#     list_display = ('user', 'review', 'vote_type')
#     list_filter = ('vote_type',)
#     search_fields = ('user__username', 'review__id')
#     ordering = ('review',)


# admin.site.register(Vote, VoteAdmin)
