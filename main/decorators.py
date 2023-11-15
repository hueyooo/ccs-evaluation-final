from django.shortcuts import redirect

def unauthenticated_user(view_func):
  def wrapper_func(request, *args, **kwargs):
    if request.user.is_authenticated:
      return redirect('/home')
    else: 
      return view_func(request, *args, **kwargs)
    
  return wrapper_func

def authenticated_user_admin(view_func):
  def wrapper_func(request, *args, **kwargs):
    if request.user.role == 'Student' or (request.user.role == 'Instructor' and(request.user.instructor.access_lvl == 1 or request.user.instructor.access_lvl == 2)):
      return redirect('/home')
    else: 
      return view_func(request, *args, **kwargs)
    
  return wrapper_func

def authenticated_user_eval(view_func):
  def wrapper_func(request, *args, **kwargs):
    if request.user.role == '':
      return redirect('/home')
    else: 
      return view_func(request, *args, **kwargs)
    
  return wrapper_func