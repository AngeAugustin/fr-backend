from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('reports', '0003_generatedfile_file_content'),
    ]
    operations = [
        migrations.RemoveField(
            model_name='generatedfile',
            name='file',
        ),
    ]
