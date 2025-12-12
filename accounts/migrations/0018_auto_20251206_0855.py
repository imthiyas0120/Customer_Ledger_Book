from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_credit_user_monthlyturnover_user_product_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='serial_no',
            field=models.PositiveIntegerField(unique=True, null=True, blank=True),
        ),
    ]
