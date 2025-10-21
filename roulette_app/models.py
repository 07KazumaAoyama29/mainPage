from django.db import models

# Create your models here.
class LabMember(models.Model):
    """研究室のメンバーを表すモデル"""
    GROUP_CHOICES = [
        ('COMM', '通信'),
        ('GRAPH', 'グラフ'),
    ]
    YEAR_CHOICES = [
        ('B4', '学部4年'),
        ('M1', '修士1年'),
        ('M2', '修士2年'),
        ('D', '博士課程'),
        ('PD', '研究員'),
        ('STAFF', '教員'),
    ]

    name = models.CharField("メンバー名", max_length=100)
    research_group = models.CharField("所属グループ", max_length=10, choices=GROUP_CHOICES)
    academic_year = models.CharField("学年", max_length=10, choices=YEAR_CHOICES, default='M1') 
    is_active = models.BooleanField("在籍中", default=True) # 卒業生などを非表示にするため

    class Meta:
        verbose_name = "研究室メンバー"
        verbose_name_plural = "研究室メンバー"

    def __str__(self):
        return f"{self.name} ({self.get_research_group_display()})"