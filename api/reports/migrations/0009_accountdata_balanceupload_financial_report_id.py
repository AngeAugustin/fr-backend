# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_remove_balanceupload_comment_generatedfile_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountData',
            fields=[
                ('id', models.CharField(max_length=36, primary_key=True, serialize=False)),
                ('account_number', models.CharField(db_index=True, max_length=20)),
                ('account_label', models.CharField(blank=True, max_length=200)),
                ('account_class', models.CharField(blank=True, max_length=10)),
                ('balance', models.DecimalField(decimal_places=2, max_digits=15)),
                ('total_debit', models.DecimalField(decimal_places=2, max_digits=15)),
                ('total_credit', models.DecimalField(decimal_places=2, max_digits=15)),
                ('entries_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(db_index=True)),
                ('financial_report_id', models.CharField(blank=True, max_length=36)),
                ('account_lookup_key', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'db_table': 'account_data',
            },
        ),
        migrations.AddIndex(
            model_name='accountdata',
            index=models.Index(fields=['account_number', 'created_at'], name='account_data_account_number_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='accountdata',
            index=models.Index(fields=['financial_report_id'], name='account_data_financial_report_id_idx'),
        ),
        migrations.AlterField(
            model_name='balanceupload',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='balances/'),
        ),
        migrations.AddField(
            model_name='balanceupload',
            name='financial_report_id',
            field=models.CharField(blank=True, max_length=36, null=True),
        ),
    ]
