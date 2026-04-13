from django.contrib import admin
from .models import Book
from .models import MainMenu

# Register your models here.

admin.site.register(MainMenu)

admin.site.register(Book)