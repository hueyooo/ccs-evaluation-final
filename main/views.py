from django.shortcuts import render, redirect
from .forms import UpdateUserForm, UpdateQuestionnaire, BulkReg, EvalSchedForm, EvalSchedFormOngoing, UpdateInstructorQuestionnaire, UpdateSubjects
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Questionnaire, InstructorQuestionnaire, Student, Instructor, EvaluatedDetails, QuestionnaireScore, Comment, Subjects, EvalSched, InstructorQuestionnaireScore
from django.contrib.auth import get_user_model, authenticate, login, logout
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from .decorators import unauthenticated_user, authenticated_user_admin, authenticated_user_eval
from django.core.files.storage import default_storage
from django.contrib.auth.hashers import make_password
from django.urls import reverse
import pandas as pd
import datetime

User = get_user_model()

#Datepicker
@login_required(login_url="/login")
@authenticated_user_admin
def evalsched(request):
  evalsched_check = EvalSched.objects.all()

  if len(evalsched_check) == 0:
    if request.method == 'POST':
      form = EvalSchedForm(request.POST)

      if form.is_valid():
        form.save()
        return redirect('/settings')
    else:
      form = EvalSchedForm()
    
    return render(
      request, 
      'main/eval_sched_set.html',
      {"form": form}
    )
  else: 
    get_eval_sched = EvalSched.objects.all()[0]
    if request.method == 'POST':
      if get_eval_sched.date_from == datetime.date.today():
        form = EvalSchedFormOngoing(
          request.POST,
          instance=get_eval_sched
        )
      else:
        form = EvalSchedForm(
          request.POST,
          instance=get_eval_sched
        )

      if form.is_valid():
        form.save()
        messages.success(request, 'Updated Successfully')
        return redirect('/settings/evaluation_sched')

    else:
      if get_eval_sched.date_from == datetime.date.today():
        form = EvalSchedFormOngoing(instance=get_eval_sched)
      else:
        form = EvalSchedForm(instance=get_eval_sched)
   
    return render(
      request, 
      'main/eval_sched_edit.html',
      {'form': form}
    )
  
#Delete Datepicker
@login_required(login_url="/login")
@authenticated_user_admin
def delete_evalsched(request):
  EvalSched.objects.all().delete()
  
  return redirect('/settings')

#Sign in
@unauthenticated_user
def loginuser(request):
  if request.method == 'POST':
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is not None:
      login(request, user)
      if request.user.role == 'Student':
        check_irreg = Student.objects.filter(user_id=request.user.id)
        if len(check_irreg) == 0:
          return redirect('/irregular')
        else:
          return redirect('home')
      else:
          return redirect('home')
    else:
      messages.success(request, 'Please enter a correct username and password. Note that both fields may be case-sensitive.')
      return redirect('/login')
  else:
    return render(
      request, 
      'registration/login.html',
    )

#Sign Out
@login_required(login_url="/login")
def logoutuser(request):
  logout(request)
  return redirect('login')

#Home
@login_required(login_url="/login")
def home(request):
  if request.user.role == 'Student':
    check_irreg = Student.objects.filter(user_id=request.user.id)
    if len(check_irreg) == 0:
      return redirect('/irregular')
  return render(
    request, 
    'main/home.html'
  )

#Sign Up
@login_required(login_url="/login")
def irreg_sign_up(request):
  check_irreg = Student.objects.filter(user_id=request.user.id)
  if len(check_irreg) > 0:
    return redirect('/home')
  sort_sec = sort_section()
  if request.method == 'POST':
    sections = request.POST['section']
    if sections:
      return redirect(reverse('irreg_sign_up_subjects', kwargs = {"sections": sections}))
    else:
      pass 
    
  return render(
    request, 
    'registration/irregular_register.html',
    {'sections': sort_sec}
  )

@login_required(login_url="/login")
def irreg_sign_up_subjects(request, sections):
  check_irreg = Student.objects.filter(user_id=request.user.id)
  if len(check_irreg) > 0:
    return redirect('/home')
  section = sections.split(', ')
  irreg_subjects = []
  for sec in section:
    get_subjects = EvaluatedDetails.objects.filter(section=sec)
    for sub in get_subjects:
      sec_sub = {"description": sub.subj.description, "code":sub.subj.code, "section":sec}
      irreg_subjects.append(sec_sub)
  if request.method == 'POST':
    subjects = request.POST['subjects']
    subject = subjects.split('\n')
    irreg_section = ''
    for sub in subject:
      sub = sub.replace('\r', '')
      if irreg_section == '':
        irreg_section = sub
      else:
        irreg_section = irreg_section + '/' + sub
    
    irregular = Student(
      user_id = request.user.id,
      section = irreg_section
    )
    irregular.save()

    return redirect('home')    
  return render(
    request, 
    'registration/irregular_register_subjects.html',
    {'subjects': irreg_subjects,
     'sections': section}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def role(request):
  getrole = 'Student'
  getrole2 = 'Instructor'
  
  return render(
    request, 
    ('registration/role.html'), 
    {"roles":getrole, 
     "rolei":getrole2
    }
  )

@login_required(login_url="/login")
@authenticated_user_admin
def sign_up(request, role):
  if request.method == 'POST':
    form = BulkReg(request.POST, request.FILES)
    file = request.FILES['file']
    # file_name = default_storage.save(file.name, file)
    # file_url = default_storage.path(file_name)
    file_check = str(file)
    if file_check.endswith('.csv'):
      df = pd.read_csv(file)
    elif file_check.endswith('.xlsx'):
      df = pd.read_excel(file)
    elif file_check.endswith('.txt'):
      df = pd.read_table(file, delimiter=",")
      print(df.columns)
    else:
      messages.success(request, 'File not supported')
      return redirect('/sign-up/%s' % role)

    if role == 'Student':
      if 'first_name' and 'last_name' and 'student_number' and 'section' in df.columns:
        missing = df.isnull().values.any()
        if missing:
          messages.success(request, 'Some values are missing from the file.')
          return redirect('/sign-up/%s' % role)
        else:
          username_found = []
          success = 0
          for data in df.values:
            first_name = data[0]
            last_name = data[1]
            student_no = str(int(data[2]))
            section = data[3]
            password = make_password(student_no)

            user_check = User.objects.all()
            skip = False
            for user in user_check:
              if user.username == student_no:
                skip = True
                break

            if skip == True:
              username_found.append(student_no)
              continue

            user_student_reg = User(
              first_name = first_name,
              last_name = last_name,
              username = student_no,
              email = student_no + "@dhvsu.edu.ph",
              password = password,
              role = role
            )
            user_student_reg.save()

            if section != 'IRREG':
              users = User.objects.all()
              for user in users:
                if user.username == student_no:
                  id = user.id
                  break
                  
              student_section = Student(
                user_id = id,
                section = section
              )
              student_section.save()

            success = success + 1

          if success != 0:
            message = 'Successfully registered ' + str(success) + ' users'
            messages.success(request, message)
          else:
            message = 'Registered none'
            messages.warning(request, message)
          if len(username_found) != 0:
            for found in username_found:
              message = 'Username already available: ' + found
              messages.warning(request, message)
      else:
        messages.warning(request, 'File is not a register file')
        return redirect('/sign-up/%s' % role)
    elif role == 'Instructor':
      if 'first_name' and 'last_name' and 'email' and 'department' and 'role' in df.columns:
        missing = df.isnull().values.any()
        if missing:
          messages.warning(request, 'Some values are missing from the file.')
          return redirect('/sign-up/%s' % role)
        else:
          username_found = []
          success = 0
          for data in df.values:
            first_name = data[0]
            last_name = data[1]
            email = data[2]
            username = data[2].replace('@dhvsu.edu.ph', '')
            department = data[3]
            access_lvl = data[4]
            password = make_password(username)

            user_check = User.objects.all()
            skip = False
            for user in user_check:
              if user.username == username:
                skip = True
                break

            if skip == True:
              username_found.append(username)
              continue

            if access_lvl == 'Dean':
              user_student_reg = User(
                first_name = first_name,
                last_name = last_name,
                username = username,
                email = email,
                password = password,
                is_superuser = True,
                role = role
              )
            else:
              user_student_reg = User(
                first_name = first_name,
                last_name = last_name,
                username = username,
                email = email,
                password = password,
                role = role
              )
            user_student_reg.save()

            users = User.objects.all()
            for user in users:
              if user.username == username:
                id = user.id
                break

            if access_lvl == 'Instructor':
              access_lvl = 1
            elif access_lvl == 'Chairperson':
              access_lvl = 2
            elif access_lvl == 'Dean':
              access_lvl = 3
                
            instructor_data = Instructor(
              user_id = id,
              department = department,
              access_lvl = access_lvl
            )
            instructor_data.save()

            success = success + 1

          if success != 0:
            print('Successfully registered ', success, ' users' )
          else:
            print('Registered none')
          if len(username_found) != 0:
            print("User already registered")
            for found in username_found:
              print(found)
      else:
        messages.warning(request, 'File is not a register file')
        return redirect('/sign-up/%s' % role)
  else:
    form = BulkReg()

  return render(
    request,
    'registration/bulkreg.html',
    {"form": form,
     "role": role}
  )

#Profile
@login_required(login_url="/login")
def update_profile(request):
  if request.method == "POST":
    form = UpdateUserForm(
      request.POST, 
      request.FILES,
      instance=request.user
    )
    if form.is_valid():
      form.save()
      return redirect('update_profile')
  else:
    form = UpdateUserForm(instance=request.user)

  return render(
    request, 
    'main/updt_profile.html', 
    {"form": form}
  )

#Evaluation
@login_required(login_url="/login")
def evaluation_select(request):
  check_completed = Comment.objects.all()
  to_eval = []
  if request.user.role == "Student":
    to_evaluate = EvaluatedDetails.objects.all()
    if ',' in request.user.student.section:
      if '/' in request.user.student.section:
        irregular = request.user.student.section.split('/')
      else:
        irregular = [request.user.student.section]
      for irreg in irregular:
        check_sub = irreg.split(',')
        for evaluate in to_evaluate:
          if check_sub[0] == evaluate.subj.code and check_sub[1] == evaluate.section:
            to_eval.append(evaluate)
    else:
      for evaluate in to_evaluate:
        if request.user.student.section == evaluate.section:
          to_eval.append(evaluate)
  elif request.user.role == "Instructor" and request.user.instructor != 3:
    to_evaluate = Instructor.objects.all()
    for evaluate in to_evaluate:
      if request.user.instructor.department == evaluate.department:
        to_eval.append(evaluate)

  if request.user.is_superuser:
    return render(
      request,
      'main/admin_evaluation.html',
      {
        "evaluate": to_eval,
        "completed": check_completed,
      }
    )
  else:
    evalsched_check = EvalSched.objects.all()
    if not evalsched_check:
      check = False
    else:
      evalsched_check = EvalSched.objects.all()[0]
      check = False
      if datetime.date.today() >= evalsched_check.date_from and datetime.date.today() <= evalsched_check.date_to:
        check = True
    return render(
      request,
      'main/evaluation.html',
      {
        "evaluate": to_eval,
        "completed": check_completed,
        "check": check
      }
    )
  
@login_required(login_url="/login")
@authenticated_user_admin
def evaluation_select_dean(request):
  check_completed = Comment.objects.all()
  to_eval = []

  to_evaluate = Instructor.objects.all()
  for evaluate in to_evaluate:
    if request.user.instructor.access_lvl == 2:
      to_eval.append(evaluate)
  
  evalsched_check = EvalSched.objects.all()
  if not evalsched_check:
    check = False
  else:
    evalsched_check = EvalSched.objects.all()[0]
    check = False
    if datetime.date.today() >= evalsched_check.date_from and datetime.date.today() <= evalsched_check.date_to:
      check = True
  return render(
    request,
    'main/evaluation.html',
    {
      "evaluate": to_eval,
      "completed": check_completed,
      "check": check
    }
  )
  

#Evaluation questionnaire submit
@login_required(login_url="/login")
@authenticated_user_eval
def questionnaire(request, evaluated):
  if request.user.role == 'Student':
    questions = Questionnaire.objects.all()
  elif request.user.role == 'Instructor':
    questions = InstructorQuestionnaire.objects.all()
  check_completed = QuestionnaireScore.objects.all()
  check_sub = EvaluatedDetails.objects.all()
  check_dept = Instructor.objects.all()

  if request.method == 'POST':
    get_question_score = []
    score_comment_checker = 0
    for question in questions:
      get_question_id = str(question.id)
      get_question_id_value = request.POST[get_question_id]
      converted_value = int(get_question_id_value)
      get_question_score.append({'score': converted_value, 'author': request.user.id, 'question': question.id, 'evaluated': evaluated})
      score_comment_checker = score_comment_checker + converted_value
    neutral_score = int((len(get_question_score) * 5)/2)
    
    print(get_question_score)
    comment = request.POST['comment']
    sentiment_analyzer = SentimentIntensityAnalyzer()
    comment_sentiment = sentiment_analyzer.polarity_scores(comment)
    if comment_sentiment['compound'] > 0.0:
      cs = 'Positive'
    elif comment_sentiment['compound']  == 0:
      cs = 'Neutral'
    elif comment_sentiment['compound']  < 0:
      cs = 'Negative'

    if cs == 'Positive' and neutral_score > score_comment_checker:
      messages.success(request, 'The scores you have give do not match with the sentiment of the comment')
      return redirect('/evaluation/%s' % evaluated)
    elif cs == 'Negative' and neutral_score < score_comment_checker:
      messages.success(request, 'The scores you have give do not match with the sentiment of the comment')
      return redirect('/evaluation/%s' % evaluated)
    else:
      for score in get_question_score:
        if request.user.role == 'Student':
          question_score = QuestionnaireScore(
            score = score['score'],
            author_id = score['author'],
            question_id = score['question'],
            evaluated_id = score['evaluated']
          )
          question_score.save()
        elif request.user.role == 'Instructor':
          question_score = InstructorQuestionnaireScore(
            score = score['score'],
            author_id = score['author'],
            question_id = score['question'],
            evaluated_id = score['evaluated']
          )
          question_score.save()

      user_comment = Comment(
        comment = comment,
        sentiment = cs,
        author_id = request.user.id,
        evaluated_id = evaluated
      )
      user_comment.save()

      if request.user.role == 'Instructor':
        if request.user.instructor.access_lvl == '3': 
          return redirect('/evaluation/dean')
        else:
          return redirect('/evaluation')
      elif request.user.role == 'Student':
        return redirect('/evaluation')

  
  for check in check_completed:
    if check.author.id == request.user.id and check.evaluated.user.id == evaluated:
      return redirect('/evaluation')
    
  checked = False
  if request.user.role == 'Student':
    if ',' in request.user.student.section:
      if '/' in request.user.student.section:
        irregular = request.user.student.section.split('/')
      else:
        irregular = [request.user.student.section]
      for irreg in irregular:
        check_irreg_sub = irreg.split(',')
        for sub in check_sub:
          if check_irreg_sub[0] == sub.subj.code and check_irreg_sub[1] == sub.section:
            if sub.inst.user.id == evaluated:
              checked = True
              break
    else:
      for sub in check_sub:
        if request.user.student.section == sub.section:
          if sub.inst.user.id == evaluated:
            checked = True
            break
  elif request.user.role == 'Instructor':
    for dept in check_dept:
      if request.user.instructor.department == dept.department:
        if dept.user.id == evaluated:
          checked = True
          break
  
  if checked == False:
    return redirect('/evaluation')

  if request.user.role == 'Student':
    return render(
      request, 
      'main/questionnaire.html', 
      {"questions": questions}
    )
  elif request.user.role == 'Instructor':
    return render(
      request, 
      'main/questionnaire_instructor.html', 
      {"questions": questions}
    )

# Edit Questionnaire
@login_required(login_url="/login")
@authenticated_user_admin
def edit_students_questionnaire(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  questions = Questionnaire.objects.all()

  return render(
    request, 
    'main/edit_students_questionnaire.html', 
    {"questions": questions}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def edit_instructors_questionnaire(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  questions = InstructorQuestionnaire.objects.all()

  return render(
    request, 
    'main/edit_instructors_questionnaire.html', 
    {"questions": questions}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def update_students_questionnaire(request, id):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  questions = Questionnaire.objects.all()
  for question in questions:
    if question.id == id:
      upd_question = question
      break

  if request.method == "POST":
    form = UpdateQuestionnaire(
      request.POST, 
      request.FILES,
      instance=upd_question
    )
    if form.is_valid():
      form.save()
      return redirect('edit_students_questionnaire')
  else:
    form = UpdateQuestionnaire(instance=upd_question)

  return render(
    request,
    'main/update_students_questionnaire.html',
    {"question": upd_question,
     "form": form}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def update_instructors_questionnaire(request, id):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  questions = InstructorQuestionnaire.objects.all()
  for question in questions:
    if question.id == id:
      upd_question = question
      break

  if request.method == "POST":
    form = UpdateInstructorQuestionnaire(
      request.POST, 
      request.FILES,
      instance=upd_question
    )
    if form.is_valid():
      form.save()
      return redirect('edit_instructors_questionnaire')
  else:
    form = UpdateInstructorQuestionnaire(instance=upd_question)

  return render(
    request,
    'main/update_instructors_questionnaire.html',
    {"question": upd_question,
     "form": form}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def add_students_questionnaire(request, category):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  if request.method == "POST":
    add_questionnaire = Questionnaire(
      category = category,
      question = request.POST['question']
    )
    add_questionnaire.save()
    return redirect('edit_students_questionnaire')

  return render(
    request,
    'main/add_students_questionnaire.html',
    {"category": category}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def add_instructors_questionnaire(request, category):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  if request.method == "POST":
    add_questionnaire = InstructorQuestionnaire(
      category = category,
      question = request.POST['question']
    )
    add_questionnaire.save()
    return redirect('edit_instructors_questionnaire')

  return render(
    request,
    'main/add_instructors_questionnaire.html',
    {"category": category}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def delete_students_questionnaire(request, id):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  question = Questionnaire.objects.get(id=id)
  question.delete()
  
  return redirect('edit_students_questionnaire')

@login_required(login_url="/login")
@authenticated_user_admin
def delete_instructors_questionnaire(request, id):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  question = InstructorQuestionnaire.objects.get(id=id)
  question.delete()
  
  return redirect('edit_instructors_questionnaire')

#View Responses
@login_required(login_url="/login")
@authenticated_user_admin
def view_responses(request):
  return render(
    request,
    'main/view_responses.html'
  )

@login_required(login_url="/login")
@authenticated_user_admin
def view_completion_chart(request):
  sort_sec = sort_section()

  users = User.objects.all()
  eval_deets = EvaluatedDetails.objects.all()
  students = Student.objects.all()
  evaluated = QuestionnaireScore.objects.all()
  get_evaluated_true = []
  get_evaluated_total = []

  for user in users:
    if user.role == 'Student':
      get_to_eval = []
      get_to_eval_irreg = []
      complete_registration = False
      for student in students:
        if user == student.user:
          complete_registration = True
          if ',' in student.section:
            if '/' in student.section:
              irregular = student.section.split('/')
            else:
              irregular = [student.section]
            for irreg in irregular:
              check_sub = irreg.split(',')
              for eval in eval_deets:
                if check_sub[0] == eval.subj.code and check_sub[1] == eval.section:
                  get_to_eval_irreg.append({'section': eval.section, 'instructor': eval.inst.user.id})
            break
          else:
            for eval in eval_deets:
              if student.section == eval.section:
                get_to_eval.append(eval.inst.user.id)
            break
      
      if complete_registration == False:
        continue

      check_completed = False
      check_completed_irreg = []
      if ',' in user.student.section:
        for get in get_to_eval_irreg:
          is_evaluated = False
          for check in evaluated:
            if user == check.author and get['instructor'] == check.evaluated.user.id:
              is_evaluated = True
              break

          if is_evaluated == False:
            check_completed = False
            check_completed_irreg.append({'section': get['section'], 'status': check_completed})
          else:
            check_completed = True
            check_completed_irreg.append({'section': get['section'], 'status': check_completed})
      else:
        for get in get_to_eval:
          is_evaluated = False
          for check in evaluated:
            if user == check.author and get == check.evaluated.user.id:
              is_evaluated = True
              break
          
          if is_evaluated == False:
            check_completed = False
            break
          else:
            check_completed = True
    
      if check_completed:
        get_evaluated_true.append(user.student.section)      

      if ',' in user.student.section:
        if '/' in user.student.section:
          irregular = user.student.section.split('/')
        else:
          irregular = [user.student.section]
        irreg_sec = []
        for irreg in irregular:
          get_sec = irreg.split(',')
          if not irreg_sec:
            get_evaluated_total.append(get_sec[1])
            irreg_sec.append(get_sec[1])
          else:
            check_if_not_appended = True
            for sec in irreg_sec:
              if sec == get_sec[1]:
                check_if_not_appended = False
                irreg_sec.append(get_sec[1])
                break
            if check_if_not_appended == True:
              get_evaluated_total.append(get_sec[1])
              irreg_sec.append(get_sec[1])
        check_total_per_sec = []
        checked = []
        for irreg_true in irregular:
          get_sec = irreg_true.split(',')
          if not checked:
            checked.append(get_sec[1])
            total_per_sec = irreg_sec.count(get_sec[1])
            check_total_per_sec.append({'section': get_sec[1], 'count': total_per_sec})
          else:
            if get_sec[1] in checked:
              continue
            else:
              checked.append(get_sec[1])
              total_per_sec = irreg_sec.count(get_sec[1])
              check_total_per_sec.append({'section': get_sec[1], 'count': total_per_sec})
        
        to_check = []
        for check in check_completed_irreg:
          if check['status'] == True:
            to_check.append(check['section'])
        
        for check in check_total_per_sec:
          if check['count'] == to_check.count(check['section']):
            get_evaluated_true.append(check['section'])
      else:
        get_evaluated_total.append(user.student.section)

  pass_evaluated_true=[]
  pass_evaluated_total=[]
  for section in get_evaluated_total:
    if not pass_evaluated_total:
      eval_total_sec = get_evaluated_total.count(section)
      pass_evaluated_total.append({'section': section, 'count': eval_total_sec})
    else:
      for to_pass in pass_evaluated_total:
        check_if_appended = False
        if to_pass['section'] == section:
          check_if_appended = True
          break
      if check_if_appended == False:
        eval_total_sec = get_evaluated_total.count(section)
        pass_evaluated_total.append({'section': section, 'count': eval_total_sec})
  
  for section_total in pass_evaluated_total:
    if section_total['section'] in get_evaluated_true:
      eval_true_sec = get_evaluated_true.count(section_total['section'])
      pass_evaluated_true.append({'section': section_total['section'], 'count': eval_true_sec})
    else:
      eval_true_sec = 0
      pass_evaluated_true.append({'section': section_total['section'], 'count': eval_true_sec})

  percentage = []
  for pass1 in pass_evaluated_total:
    for pass2 in pass_evaluated_true:
      if pass1['section'] == pass2['section']:
        percent = pass2['count']/pass1['count'] * 100
        percent = "{:.2f}".format(percent)
        percentage.append({'section':pass1['section'], 'percent': percent})


  return render(
    request,
    'main/view_completion_chart.html',
    {'section': sort_sec,
     'value': pass_evaluated_true,
     'total': pass_evaluated_total,
     'percentage': percentage}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def view_instructor_chart(request):
  return render(
    request,
    'main/view_instructor_chart.html'
  )

def sort_section():
  sections = Student.objects.all()
  section_array = []

  for section in sections:
    is_found = False
    for check in section_array:
      if section.section == check:
        is_found = True
        break
    
    if is_found == False:
      section_array.append(section.section)

  course = ['IT','IS','CS','ACT']
  year = ['1','2','3','4']
  sect = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
  sort_section = []

  for crs in course:
    for yr in year:
      for sec in sect:
        check_var = crs + "-" + yr + sec
        is_found = False
        for section in section_array:
          if section == check_var:
            is_found = True
            break
        
        if is_found == True:
          sort_section.append(check_var)
  
  return sort_section

@login_required(login_url="/login")
@authenticated_user_admin
def view_instructor_chart_student(request):
  instructors = Instructor.objects.all()

  return render(
    request,
    'main/view_instructor_studeval.html',
    {'instructor': instructors}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def view_instructor_chart_instructor(request):
  instructors = Instructor.objects.all()

  return render(
    request,
    'main/view_instructor_insteval.html',
    {'instructor': instructors}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def view_instructor_chart_id_student(request, id):
  instructor = Instructor.objects.get(user_id=id)
  instructor_check = Instructor.objects.all()
  questions = Questionnaire.objects.all()
  scores = QuestionnaireScore.objects.all()
  comments = Comment.objects.filter(evaluated_id=id)
  question_average = []

  for question in questions:
    question_score = 0
    question_score_total_eval = 0
    for score in scores:
      if instructor.user.id == score.evaluated_id and score.question == question:
        question_score += score.score
        question_score_total_eval += 1
    if question_score_total_eval == 0:
      ave = 'N/A'
    else:
      average = question_score/question_score_total_eval
      ave = "{:.2f}".format(average)
    question_average.append({'category': question.category, 'question': question.question, 'average': ave})

  comment_counter = 0
  comment_positive = 0
  comment_negative = 0
  comment_neutral = 0
  comment_students = []

  if len(comments) != 0:
    for comment in comments:
      check = False
      for inst in instructor_check:
        if comment.author == inst:
          check = True
          break
      if check == False:
        if comment.sentiment == 'Positive':
          comment_positive = comment_positive + 1
          comment_counter = comment_counter + 1
        elif comment.sentiment == 'Neutral':
          comment_neutral = comment_neutral + 1
          comment_counter = comment_counter + 1
        elif comment.sentiment == 'Negative':
          comment_negative = comment_negative + 1
          comment_counter = comment_counter + 1
        comment_students.append(comment)
  
    comment_total = comment_counter * 2
    comment_value = comment_counter + comment_positive - comment_negative
    sentiment = comment_value/comment_total * 100
    sentiment = "{:.2f}".format(sentiment)
    sentiment = float(sentiment)
  else:
    sentiment = 50

  return render(
    request,
    'main/view_instructor_charts_students.html',
    {'instructor': instructor,
     'average': question_average,
     'sentiment': sentiment,
     'comments': comment_students,
     'comment_number': comment_counter}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def view_instructor_chart_id_instructor(request, id):
  instructor = Instructor.objects.get(user_id=id)
  instructor_check = Instructor.objects.all()
  questions = InstructorQuestionnaire.objects.all()
  scores = InstructorQuestionnaireScore.objects.all()
  comments = Comment.objects.filter(evaluated_id=id)
  question_average = []

  for question in questions:
    question_score = 0
    question_score_total_eval = 0
    for score in scores:
      if instructor.user.id == score.evaluated_id and score.question == question:
        question_score += score.score
        question_score_total_eval += 1
    if question_score_total_eval == 0:
      ave = 'N/A'
    else:
      average = question_score/question_score_total_eval
      ave = "{:.2f}".format(average)
    question_average.append({'category': question.category, 'question': question.question, 'average': ave})

  comment_counter = 0
  comment_positive = 0
  comment_negative = 0
  comment_neutral = 0
  comment_students = []

  if len(comments) != 0:
    print(len(comments))
    for comment in comments:
      for inst in instructor_check:
        if comment.author == inst:
          if comment.sentiment == 'Positive':
            comment_positive = comment_positive + 1
            comment_counter = comment_counter + 1
          elif comment.sentiment == 'Neutral':
            comment_neutral = comment_neutral + 1
            comment_counter = comment_counter + 1
          elif comment.sentiment == 'Negative':
            comment_negative = comment_negative + 1
            comment_counter = comment_counter + 1
          comment_students.append(comment)
    if comment_counter != 0:
      comment_total = comment_counter * 2
      comment_value = comment_counter + comment_positive - comment_negative
      sentiment = comment_value/comment_total * 100
      sentiment = "{:.2f}".format(sentiment)
      sentiment = float(sentiment)
    else:
      sentiment = 50
  else:
    sentiment = 50

  return render(
    request,
    'main/view_instructor_charts_instructors.html',
    {'instructor': instructor,
     'average': question_average,
     'sentiment': sentiment,
     'comments': comment_students,
     'comment_number': comment_counter}
  )

#Edit Instructor per Section
@login_required(login_url="/login")
@authenticated_user_admin
def edit_choice(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')

  return render(
    request,
    'main/edit_choice.html'
  )

@login_required(login_url="/login")
@authenticated_user_admin
def add_bulk_instructor_per_section(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')

  if request.method == 'POST':
    form = BulkReg(request.POST, request.FILES)
    file = request.FILES['file']
    # file_name = default_storage.save(file.name, file)
    # file_url = default_storage.path(file_name)
    file_check = str(file)
    if file_check.endswith('.csv'):
      df = pd.read_csv(file)
    elif file_check.endswith('.xlsx'):
      df = pd.read_excel(file)
    elif file_check.endswith('.txt'):
      df = pd.read_table(file, delimiter=",")
      print(df.columns)
    else:
      messages.warning(request, 'File not supported')
      return redirect('add_bulk_instructor_per_section')

    check_instructor = Instructor.objects.all()
    check_subjects = Subjects.objects.all()
    check_eval_deets = EvaluatedDetails.objects.all()

    if 'section' and 'instructor_first_name' and 'instructor_last_name' and 'subject_code' in df.columns:
      missing = df.isnull().values.any()
      if missing:
        messages.warning(request, 'Some values are missing from the file.')
        return redirect('add_bulk_instructor_per_section')
      else:
        failed_values = []
        success = 0
        for data in df.values:
          section = data[0]
          instructor = data[1] + ' ' + data[2]
          subject = data[3]
          skip = True

          for eval in check_eval_deets:
            instructor_check = eval.inst.user.first_name + ' ' + eval.inst.user.last_name
            if eval.section == section and instructor_check == instructor and eval.subj.code == subject:
              if instructor_check == instructor:
                if eval.subj.code == subject:
                  skip = False
                  break

          if skip == False:
            failed_values.append(data)
            continue

          skip = True

          for inst in check_instructor:
            instructor_check = inst.user.first_name + ' ' + inst.user.last_name
            if instructor_check == instructor:
              instructor = inst.user.id
              for subj in check_subjects:
                if subj.code == subject:
                  subject = subj.id
                  skip = False
                  break
              break
          
          if skip == True:
            failed_values.append(data)
            continue

          evaluated_deets = EvaluatedDetails(
            section = section,
            inst_id = instructor,
            subj_id = subject,
          )
          evaluated_deets.save()

          success = success + 1

        if success != 0:
          message = 'Successfully registered ' + str(success) + ' users'
          messages.success(request, message)
        else:
          message = 'Registered none'
          messages.warning(request, message)
        if len(failed_values) != 0:
          for found in failed_values:
            message = 'Failed to register ' + found[0] + found[3] + ' instructor/s per section'
            messages.warning(request, message)
    else:
      messages.warning(request, 'File is not a register file')
      return redirect('add_bulk_instructor_per_section')
  else:
    form = BulkReg()

  return render(
    request,
    'main/add_instructors_bulk.html',
    {"form": form}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def edit_instructor(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  sort_sec = sort_section()

  return render(
    request,
    'main/edit_instructor.html',
    {'section': sort_sec}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def edit_instructor_per_section(request, section):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  inst_per_sec = EvaluatedDetails.objects.all()
  instructors = []

  for inst in inst_per_sec:
    if inst.section == section:
      instructors.append(inst)

  return render(
    request,
    'main/edit_instructor_per_sec.html',
    {'instructor': instructors,
     'section':section}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def edit_instructor_per_id(request, section, id):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  instructor = EvaluatedDetails.objects.all()
  instructors = Instructor.objects.all()
  subjects = Subjects.objects.all()

  for inst in instructor:
    if inst.section == section and inst.inst.user.id == id:
      instance = inst
      break

  if request.method == 'POST':
    get_instructor = EvaluatedDetails.objects.get(id=inst.id)
    get_instructor_id = int(request.POST['instructor'])
    get_sub_id = int(request.POST['subject'])
    get_instructor.inst_id = get_instructor_id
    get_instructor.subj_id = get_sub_id
    get_instructor.save()
    return redirect('edit_instructor_per_section', section=section)

  return render(
    request,
    'main/edit_instructor_per_id.html',
    {'instructor': instance,
     'instructors': instructors,
     'subjects': subjects,
     'section':section}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def delete_instructor_per_id(request, id, section):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  intructor_per_sub = EvaluatedDetails.objects.get(id=id)
  intructor_per_sub.delete()
  
  return redirect('edit_instructor_per_section', section=section)

@login_required(login_url="/login")
@authenticated_user_admin
def add_instructor(request, section):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  instructors = Instructor.objects.all()
  subjects = Subjects.objects.all()

  if request.method == "POST":
    add_instructor_per_sub = EvaluatedDetails(
      section = section,
      subj_id = int(request.POST['subject']),
      inst_id = int(request.POST['instructor'])
    )
    add_instructor_per_sub.save()
    return redirect('edit_instructor_per_section', section=section)

  return render(
    request,
    'main/add_instructor.html',
    { 'instructors': instructors,
      'subjects': subjects,
      'section': section }
  )

#View/Edit Subjects
@login_required(login_url="/login")
@authenticated_user_admin
def view_subjects(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')

  subjects = Subjects.objects.all()

  return render(
    request,
    'main/view_subjects.html',
    {"subjects": subjects}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def edit_subjects(request, id):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')

  subjects = Subjects.objects.get(id=id)
  if request.method == 'POST':
    form = UpdateSubjects(
      request.POST,
      instance=subjects
    )
    if form.is_valid():
      form.save()
      return redirect('view_subjects')
  else:
    form = UpdateSubjects(instance=subjects)
  return render(
    request,
    'main/edit_subjects.html',
    {'form': form}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def delete_subjects(request, id):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')

  subjects = Subjects.objects.get(id=id)
  subjects.delete()
  
  return redirect('view_subjects')

@login_required(login_url="/login")
@authenticated_user_admin
def add_subjects_pick(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')

  return render(
    request,
    'main/add_subjects_pick.html'
  )

@login_required(login_url="/login")
@authenticated_user_admin
def add_subjects_single(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')
  if request.method == 'POST':
    form = UpdateSubjects(request.POST)
    if form.is_valid():
      form.save()
      return redirect('view_subjects')
  else:
    form = UpdateSubjects()

  return render(
    request,
    'main/add_subjects_single.html',
    {"form": form}
  )

@login_required(login_url="/login")
@authenticated_user_admin
def add_subjects_bulk(request):
  check_evalsched = EvalSched.objects.all()
  if check_evalsched:
    check_evalsched = EvalSched.objects.all()[0]
    if datetime.date.today() >= check_evalsched.date_from and datetime.date.today() <= check_evalsched.date_to:
      return redirect('/evaluation')

  if request.method == 'POST':
    form = BulkReg(request.POST, request.FILES)
    file = request.FILES['file']
    # file_name = default_storage.save(file.name, file)
    # file_url = default_storage.path(file_name)
    file_check = str(file)
    if file_check.endswith('.csv'):
      df = pd.read_csv(file)
    elif file_check.endswith('.xlsx'):
      df = pd.read_excel(file)
    elif file_check.endswith('.txt'):
      df = pd.read_table(file, delimiter=",")
      print(df.columns)
    else:
      messages.warning(request, 'File not supported')
      return redirect('add_subjects_bulk')

    check_subjects = Subjects.objects.all()

    if 'description' and 'code' in df.columns:
      missing = df.isnull().values.any()
      if missing:
        messages.warning(request, 'Some values are missing from the file.')
        return redirect('add_subjects_bulk')
      else:
        subject_found = []
        success = 0
        for data in df.values:
          description = data[0]
          code = data[1]
          skip = False
          for sub in check_subjects:
            if sub.code == code:
              skip = True
              break

          if skip == True:
            subject_found.append(description)
            continue

          subjects_added = Subjects(
            code = code,
            description = description
          )
          subjects_added.save()

          success = success + 1

        if success != 0:
          message = 'Successfully added ' + str(success) + ' subjects'
          messages.success(request, message)
        else:
          message = 'Added none'
          messages.warning(request, message)
        if len(subject_found) != 0:
          for found in subject_found:
            message = 'Subject (' + found + ') is already in the database.'
            messages.warning(request, message)
    else:
      messages.warning(request, 'File is not a register file')
      return redirect('add_subjects_bulk')
  else:
    form = BulkReg()

  return render(
    request,
    'main/add_subjects_bulk.html',
    {"form": form}
  )




#Settings
@login_required(login_url="/login")
@authenticated_user_admin
def settings(request):
  evalsched_check = EvalSched.objects.all()
  check = len(evalsched_check)

  return render(
    request,
    'main/settings.html',
    {'check': check}
  )