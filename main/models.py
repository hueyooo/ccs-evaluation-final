from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
  image = models.ImageField(
    default='default.jpg', 
    upload_to='profile_pics'
  )
  role = models.CharField(max_length=10)

  def __str__(self):
    return self.first_name + " " + self.last_name

class Student(models.Model):
  user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    primary_key=True,
  )
  sections = [
    ('IT-1A','IT-1A'),
    ('IT-1B','IT-1B'),
    ('IT-1C','IT-1C'),
    ('IT-1D','IT-1D'),
    ('IT-1E','IT-1E'),
    ('IT-1F','IT-1F'),
    ('IT-1G','IT-1G'),
    ('IT-3B','IT-3B')
  ]
  section = models.CharField(
    max_length=1000, 
    choices=sections
  )

  def __str__(self):
    return self.user.first_name + " " + self.user.last_name

class Instructor(models.Model):
  user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    primary_key=True,
  )
  departments = [
    ('IT','Information Technology'),
    ('CS/IS/ACT','Computer Science/Information System/Associate in Computer Technology')
  ]
  department = models.CharField(
    max_length=50, 
    choices=departments
  )
  access = [
    (1,'Instructor'),
    (2,'Chairperson'),
    (3,'Dean')
  ]
  access_lvl = models.IntegerField(choices=access)

  def __str__(self):
    return self.user.first_name + " " + self.user.last_name

class Subjects(models.Model):
  code = models.CharField(max_length=50)
  description = models.CharField(max_length=100)

  def __str__(self):
    return self.code + "/" + self.description
  
class EvaluatedDetails(models.Model):
  sections = [
    ('IT-1A','IT-1A'),
    ('IT-1B','IT-1B'),
    ('IT-1C','IT-1C')
  ]
  section = models.CharField(
    max_length=10, 
    choices=sections
  )
  inst = models.ForeignKey(
    Instructor, 
    on_delete=models.CASCADE
  )
  subj = models.ForeignKey(
    Subjects, 
    on_delete=models.CASCADE
  )

class Questionnaire(models.Model):
  category = models.CharField(max_length=50)
  question = models.CharField(max_length=500)

class InstructorQuestionnaire(models.Model):
  category = models.CharField(max_length=50)
  question = models.CharField(max_length=500)

class QuestionnaireScore(models.Model):
  question = models.ForeignKey(
    Questionnaire, 
    on_delete=models.CASCADE
  )
  score = models.IntegerField()
  author = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
  )
  evaluated = models.ForeignKey(
    Instructor,
    on_delete=models.CASCADE,
  )

class InstructorQuestionnaireScore(models.Model):
  question = models.ForeignKey(
    Questionnaire, 
    on_delete=models.CASCADE
  )
  score = models.IntegerField()
  author = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
  )
  evaluated = models.ForeignKey(
    Instructor,
    on_delete=models.CASCADE,
  )

class Comment(models.Model):
  comment = models.TextField()
  sentiment = models.CharField(max_length=10)
  author = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
  )
  evaluated = models.ForeignKey(
    Instructor,
    on_delete=models.CASCADE,
  )

class EvalSched(models.Model):
  date_from = models.DateField()
  date_to = models.DateField()