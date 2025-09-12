from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('reports', '0002_balanceupload_summary_data'),
    ]
    operations = [
        migrations.AddField(
            model_name='generatedfile',
            name='file_content',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='generatedfile',
            name='file',
            field=models.FileField(upload_to='generated/', blank=True, null=True),
        ),
    ]
