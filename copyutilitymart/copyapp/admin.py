from django.contrib import admin
from copyapp.models import Contact,Product,Orders,OrderUpdate,Category
# Register your models here.

admin.site.register(Contact)
admin.site.register(Product)
admin.site.register(Orders)
admin.site.register(OrderUpdate)
admin.site.register(Category)