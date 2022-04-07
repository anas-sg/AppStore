from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponse
import logging
from sys import stderr

logger = logging.getLogger("logger")

def index(request):
    """Shows the main page"""
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    request.session['name'] = request.session.get('name', None)
    ## Delete tutor
    if request.POST:
        if request.POST['action'] == 'delete':
            student_id, module_code = request.POST['student_id_mod_code'].split('_')
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM tutors WHERE student_id = %s AND module_code =  %s", [student_id, module_code])
    elif request.GET:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tutors WHERE module_code = %s", [request.GET['module_code']])
            tutors = cursor.fetchall()
        result_dict = {'records': tutors}
        return render(request,'app/index.html', result_dict)
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tutors ORDER BY module_code")
        tutors = cursor.fetchall()
    result_dict = {'records': tutors, **request.session}
    return render(request,'app/index.html', result_dict)

def view(request, student_id_mod_code):
    """Shows the view of a tutor"""
    student_id, module_code = student_id_mod_code.split('_')
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    request.session['name'] = request.session.get('name', None)
    ## Use raw query to get a tutor
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tutors WHERE student_id = %s AND module_code = %s", [student_id, module_code])
        tutor = cursor.fetchone()
        cursor.execute("SELECT module_name FROM modules WHERE module_code = %s", [module_code])
        module = cursor.fetchone()        
    result_dict = {'record': tutor, 'module': module, **request.session}
    return render(request, 'app/view.html', result_dict)

# Create your views here.
def add_tutor(request, filled):
    """Shows the add_tutor page"""
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    request.session['name'] = request.session.get('name', None)
    request.session['filled'] = bool(filled)
    if not request.session['login']:
        return HttpResponse(reason="Not logged in", status=401)
    status = 0
    if request.POST:
        ## Check if user already a tutor
        with connection.cursor() as cursor:
            query = "SELECT * FROM tutors WHERE student_id = %s AND module_code = %s"
            cursor.execute(query, [request.POST['student_id'], request.POST['module_code']])
            tutor = cursor.fetchone()
            if not tutor:
                make_tutor_op = "INSERT INTO tutors VALUES (%s, %s, %s, %s, %s, %s, %s)"
                tutor_values = [request.POST['student_id'], request.POST['name'], request.POST['module_code']
                        , request.POST['grade'], request.POST['fee'], request.POST['unit_time'], request.POST['year']]
                cursor.execute(make_tutor_op, tutor_values)
                status = 1   
            else:
                status = 2
    with connection.cursor() as cursor:
        if request.session['filled']:
            cursor.execute("SELECT name FROM users WHERE student_id = %s", [request.session['student_id']])
            tutor = cursor.fetchone()
        cursor.execute("SELECT module_code, module_name FROM modules")
        modules = cursor.fetchall()
    context = {"status": status, "modules": modules, **request.session}
    if request.session['filled']:
        context["tutor"] = tutor
    return render(request, "app/add_tutor.html", context)

# Create your views here.
def add_user(request):
    """Shows the add_user page"""
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    request.session['name'] = request.session.get('name', None)
    context = {"status": 0, **request.session}
    if request.POST:
        ## Check if student_id is already in the table
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE student_id = %s", [request.POST['student_id']])
            user = cursor.fetchone()
            if not user:
                cursor.execute("INSERT INTO users VALUES (%s, %s, %s, %s)",
                    [request.POST['student_id'], request.POST['name'],
                    bool(request.POST.get('is_admin', 'False')),
                    request.POST['password']])
                context["status"] = 1
                if not request.session['login']:
                    request.session['login'] = True
                    request.session['student_id'] = request.POST['student_id']
                    request.session['name'] = request.POST['name']   
            else:
                context["status"] = 2
                status = 'User with ID %s already exists' % (request.POST['student_id']) 
    return render(request, "app/add_user.html", context)

# Create your views here.
def edit(request, student_id_mod_code):
    """Shows the edit page"""
    student_id, module_code = student_id_mod_code.split('_')
    request.session['admin'] = request.session.get('admin', False)
    request.session['name'] = request.session.get('name', None)
    if not request.session['admin'] and request.session['student_id'] != student_id:
        return HttpResponse(reason="Not logged in", status=401)
    updated = False
    if request.POST:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE tutors SET fee = %s, unit_time = %s WHERE student_id = %s AND module_code = %s",
                           [request.POST['fee'], request.POST['unit_time'], student_id, module_code])
        updated = True
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tutors WHERE student_id = %s AND module_code = %s", [student_id, module_code])
        tutor = cursor.fetchone()
        cursor.execute("SELECT module_name FROM modules WHERE module_code = %s", [module_code])
        module = cursor.fetchone()
    if updated:
        return render(request, 'app/view.html', {
            'record': tutor, 'module': module, **request.session
        })  
    return render(request, "app/edit.html", {
        'record': tutor, 'module': module, **request.session, 'updated': updated
    })

def login(request):
    """Shows the login page"""
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    request.session['name'] = request.session.get('name', None)
    if request.session['login']:
        return redirect('index')
    context = {"status": 0}
    # Delete tutor not user
    if request.POST:
        student_id, password = request.POST['student_id'], request.POST['password']
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE student_id = %s", [student_id])
            user = cursor.fetchone()
            if user:
                if user[3] == password:
                    context["status"] = 1   #logged in
                    request.session['login'] = True
                    request.session['student_id'] = student_id
                    request.session['name'] = user[1]
                    if user[2]:
                        request.session['admin'] = True
                    return redirect('index')
                else:
                    context["status"] = 2   #wrong password                
            else:
                context["status"] = 3       #user not found
    return render(request,'app/login.html', context)

def logout(request):
    request.session['login'] = False
    request.session['admin'] = False
    request.session['student_id'] = None
    request.session['name'] = None
    return redirect('index')

def profile(request, student_id):
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    request.session['student_id'] = request.session.get('student_id', None)
    request.session['name'] = request.session.get('name', None)
    if request.POST:
        if request.POST['action'] == 'delete':
            if not request.session['login']:
                return HttpResponse(reason="Not logged in", status=401)
            elif not request.session['admin'] and request.session['student_id'] != student_id:
                return HttpResponse(reason="Not logged in", status=403)
            student_id, module_code = request.POST['student_id_mod_code'].split('_')
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM tutors WHERE student_id = %s AND module_code =  %s", [student_id, module_code])
        elif request.POST['action'] == 'accept' or request.POST['action'] == 'reject':
            module_code, tutor_id, tutee_id = request.POST['mod_tutor_tutee'].split('_')
            with connection.cursor() as cursor:
                cursor.execute("UPDATE offers SET status = %s WHERE module_code = %s AND tutor_id = %s AND tutee_id = %s",
                           [request.POST['action'] + 'ed', module_code, tutor_id, tutee_id])
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tutors WHERE student_id = %s", [student_id])
        tutors = cursor.fetchall()
        cursor.execute("""SELECT o.module_code, u.name, o.status, o.fee, o.tutee_id FROM offers o, users u
                          WHERE o.tutor_id = %s AND o.tutee_id = u.student_id""", [student_id])
        received = cursor.fetchall()
        cursor.execute("""SELECT o.module_code, u.name, o.status, o.fee FROM offers o, users u
                          WHERE o.tutee_id = %s AND o.tutor_id = u.student_id""", [student_id])
        sent = cursor.fetchall()
        cursor.execute("SELECT name FROM users WHERE student_id = %s", [student_id])
        tutorname = cursor.fetchone()[0]
    return render(request,'app/profile.html', {
        'records': tutors, 'received': received, 'sent': sent, 'tutorname': tutorname, 'visitor': request.session['student_id'] != student_id, **request.session
    })

def test(request):
    request.session['visits'] = int(request.session.get('visits', 0)) + 1
    return render(request,'app/test.html', {
        'visits': request.session['visits']
    })

def users(request):
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    if not request.session['admin']:
        return HttpResponse(reason="Not logged in", status=401)
    if request.POST:
        if 'admin' in request.POST:
            student_id = request.POST['admin']
            is_admin = True  
        else:
            student_id = request.POST['user']
            is_admin = False
        with connection.cursor() as cursor:
            cursor.execute("UPDATE users SET is_admin = %s WHERE student_id = %s", [is_admin, student_id])
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users ORDER BY name")
        users = cursor.fetchall()
    return render(request,'app/users.html', {
        'users': users, **request.session
    })

def edit_user(request, student_id):
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    if not request.session['login']:
        return HttpResponse(reason="Not logged in", status=401)
    if not request.session['admin'] and request.session['student_id'] != student_id:
        return HttpResponse(reason="Not authorised", status=403)
    status = 0
    if request.POST:
        with connection.cursor() as cursor:
            if request.session['admin']:
                cursor.execute("UPDATE users SET is_admin = %s, password = %s WHERE student_id = %s", [request.POST['is_admin'], request.POST['password'], student_id])
            else:
                cursor.execute("UPDATE users SET password = %s WHERE student_id = %s", [request.POST['password'], student_id])
            status = 1
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE student_id = %s", [student_id])
        user = cursor.fetchone()
    return render(request,'app/edit_user.html', {
        'user': user, 'status': status, **request.session
    })

def modules(request):
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    checked = False
    if request.GET and "most-tutors" in request.GET:
        with connection.cursor() as cursor:
            cursor.execute('''SELECT t.module_code, m.module_name, COUNT(*)
                              FROM tutors t, modules m
                              WHERE t.module_code = m.module_code
                              GROUP BY t.module_code, m.module_name
                              HAVING COUNT(*) >= ALL(
                              SELECT COUNT(*)
                                  FROM tutors
                                  GROUP BY module_code
                              )
                              ORDER BY t.module_code, m.module_name''')
            modules = cursor.fetchall()
            checked = True
    else:
        with connection.cursor() as cursor:
            cursor.execute('''SELECT t.module_code, m.module_name, COUNT(*)
                              FROM tutors t, modules m
                              WHERE t.module_code = m.module_code
                              GROUP BY t.module_code, m.module_name
                              ORDER BY t.module_code, m.module_name''')
            modules = cursor.fetchall()
    return render(request,'app/modules.html', {
        'modules': modules, 'num': len(modules), 'checked': checked, **request.session
    })

def search(request):
    request.session['login'] = request.session.get('login', False)
    request.session['admin'] = request.session.get('admin', False)
    if request.GET:
        with connection.cursor() as cursor:
            query = 'SELECT * FROM tutors WHERE '
            queries = []
            fields = []
            try:
                if request.GET['year']:
                    queries.append('year = %s')
                    fields.append(request.GET['year'])
            except KeyError:
                pass
            try:
                if request.GET['module_code']:
                    queries.append('module_code = %s')
                    fields.append(request.GET['module_code'])
            except KeyError:
                pass
            try:
                if request.GET['grade']:
                    queries.append('grade = %s')
                    fields.append(request.GET['grade'])
            except KeyError:
                pass
            try:
                if request.GET['unit_time']:
                    queries.append('unit_time = %s')
                    fields.append(request.GET['unit_time'])
            except KeyError:
                pass
            try:
                if request.GET['min_fee'] and request.GET['max_fee']:
                    queries.append('fee BETWEEN %s AND %s')
                    fields += [request.GET['min_fee'], request.GET['max_fee']]
            except KeyError:
                pass
            query += ' AND '.join(queries)
            try:
                if request.GET['best-value']:
                    query += ' ORDER BY grade ASC, fee ASC'
            except KeyError:
                pass
            cursor.execute(query, fields)
            results = cursor.fetchall()
        return render(request,'app/search.html', {
            'results': results, 'num': len(results), 'is_results': True, **request.session
        })
    with connection.cursor() as cursor:
        cursor.execute("SELECT module_code, module_name FROM modules ORDER BY module_code")
        modules = cursor.fetchall()
        cursor.execute("SELECT MIN(fee) FROM tutors")
        min_fee = cursor.fetchone()
        cursor.execute("SELECT MAX(fee) FROM tutors")
        max_fee = cursor.fetchone()
    return render(request,'app/search.html', {
        'modules': modules, 'min_fee': min_fee, 'max_fee': max_fee, 'is_results': False, **request.session
    })

def offer(request, mod_tutor_tutee):
    request.session['login'] = request.session.get('login', False)
    if not request.session['login']:
        return HttpResponse(reason="Not logged in", status=401)
    module_code, tutor_id, tutee_id = mod_tutor_tutee.split('_')
    status = 0
    if request.POST:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO offers VALUES (%s, %s, %s, %s, %s)",
                    [request.POST['module_code'], request.POST['tutor_id'], 
                    request.POST['tutee_id'], 'pending', request.POST['fee']])
            status = 1
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t.module_code, m.module_name, t.name, t.fee, t.unit_time, t.student_id
                          FROM tutors t, modules m
                          WHERE t.student_id = %s AND t.module_code = %s AND m.module_code = %s""", [tutor_id, module_code, module_code])
        tutor = cursor.fetchone()
    return render(request,'app/offer.html', {
        'tutor': tutor, 'status': status, **request.session
    })
