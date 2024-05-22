from django.db import migrations


def eliminar_objetos(apps, schema_editor):
    Product = apps.get_model("backend", "Product")
    Restaurant = apps.get_model("backend", "Restaurant")

    restaurant = Restaurant.objects.get(name="Eden", address="Calle Falsa 123", phone_number="1144554455")
    Product.objects.filter(restaurant=restaurant).delete()
    restaurant.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0003_alter_group_name_alter_user_username'),
    ]

    operations = [
        migrations.RunPython(eliminar_objetos),
    ]
