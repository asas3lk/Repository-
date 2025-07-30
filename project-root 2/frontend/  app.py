from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import os

app = Flask(__name__)

# =========================================================
# 1. إعدادات قاعدة البيانات - قم بتغيير هذا لـ Railway PostgreSQL
# =========================================================
# قم بتغيير هذا السطر إلى سلسلة الاتصال التي حصلت عليها من Railway
# مثال: 'postgresql://user:password@host:port/database_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:[YOUR-PASSWORD]@db.arhlulgoxamjdcgxpcfw.supabase.co:5432/postgres' # <--- غيّر هذا السطر
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Ue$v/_6!cU_TLv*

' # غيّر هذا المفتاح السري!

db = SQLAlchemy(app)

# =========================================================
# 2. تعريف نماذج قاعدة البيانات (Database Models) - مع التحسينات
# =========================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'teacher', 'student'
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)

    # علاقات مع cascade للحذف التلقائي للسجلات المرتبطة
    student = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    teacher = db.relationship('Teacher', backref='user', uselist=False, cascade="all, delete-orphan")
    admin = db.relationship('Admin', backref='user', uselist=False, cascade="all, delete-orphan") # أضفنا Admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), unique=True, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True) # يمكن أن يكون الطالب بدون صف مبدئياً
    date_of_birth = db.Column(db.Date, nullable=True)
    parent_name = db.Column(db.String(100), nullable=True)
    parent_phone = db.Column(db.String(20), nullable=True)

    grades = db.relationship('Grade', backref='student', lazy=True, cascade="all, delete-orphan")
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade="all, delete-orphan") # علاقة مع سجلات الحضور

    def __repr__(self):
        return f'<Student {self.user.first_name} {self.user.last_name}>'

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    hire_date = db.Column(db.Date, nullable=True)

    # علاقات متعدد لمتعدد مع الصفوف والمواد
    taught_classes = db.relationship('Class', secondary='class_teacher_association', backref='teachers')
    taught_subjects = db.relationship('Subject', secondary='teacher_subject_association', backref='teachers')

    grades_assigned = db.relationship('Grade', backref='teacher_obj', lazy=True) # الدرجات التي رصدها هذا المعلم
    attendance_taken = db.relationship('Attendance', backref='teacher_obj', lazy=True) # سجلات الحضور التي سجلها هذا المعلم

    def __repr__(self):
        return f'<Teacher {self.user.first_name} {self.user.last_name}>'

class Admin(db.Model): # نموذج جديد للمدير
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), unique=True, nullable=False)
    # يمكن إضافة حقول خاصة بالمدير هنا إن وجدت (مثلاً: department)

    def __repr__(self):
        return f'<Admin {self.user.first_name} {self.user.last_name}>'

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=True) # مثلاً 2025

    students = db.relationship('Student', backref='class_obj', lazy=True) # الطلاب في هذا الصف
    # علاقة متعدد لمتعدد مع المواد التي تدرس في هذا الصف
    subjects_taught_in_class = db.relationship('Subject', secondary='class_subject_association', backref='classes_offering')

    def __repr__(self):
        return f'<Class {self.name}>'

# جداول الربط (Association Tables) للعلاقات Many-to-Many
class_teacher_association = db.Table('class_teacher_association',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True)
)

teacher_subject_association = db.Table('teacher_subject_association',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True)
)

class_subject_association = db.Table('class_subject_association',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True)
)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # teacher_id تم إزالته هنا لأنه سيتم التعامل معه عبر Many-to-Many

    grades = db.relationship('Grade', backref='subject_obj', lazy=True) # الدرجات المرتبطة بهذه المادة

    def __repr__(self):
        return f'<Subject {self.name}>'

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False) # المعلم الذي رصد الدرجة
    assessment_type = db.Column(db.String(50), nullable=True) # يمكن أن يكون nullable
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)

    # تحديد العلاقات بشكل صريح
    # student = db.relationship('Student', backref='grades_received', foreign_keys=[student_id]) # هذا تم تعريفه في Student
    # subject = db.relationship('Subject', backref='grades_given', foreign_keys=[subject_id]) # هذا تم تعريفه في Subject
    # teacher = db.relationship('Teacher', backref='grades_recorded', foreign_keys=[teacher_id]) # هذا تم تعريفه في Teacher

    def __repr__(self):
        return f'<Grade {self.score}/{self.max_score} for Student {self.student_id} in {self.subject_obj.name}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True) # يمكن ربط الحضور بمادة معينة
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True) # المعلم الذي سجل الحضور
    date = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(20), nullable=False) # 'present', 'absent', 'excused'

    def __repr__(self):
        return f'<Attendance for Student {self.student_id} on {self.date}: {self.status}>'

# =========================================================
# 3. API نقاط النهاية - مع التحسينات
# =========================================================

# تسجيل دخول
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        return jsonify({'message': 'Login successful', 'role': user.role, 'user_id': user.id}), 200
    return jsonify({'message': 'Invalid username or password'}), 401

# تسجيل خروج
@app.route('/api/logout', methods=['GET'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# نقطة نهاية للتحقق من صلاحيات المدير (تستخدمها الواجهة الأمامية لصفحة التسجيل)
@app.route('/api/check_admin', methods=['GET'])
def check_admin_status():
    if 'user_id' in session and session.get('role') == 'admin':
        return jsonify({'is_admin': True}), 200
    return jsonify({'is_admin': False, 'message': 'Not authorized as admin'}), 403

# إضافة طالب جديد (admin فقط)
@app.route('/api/students', methods=['POST'])
def add_student():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'message': 'Unauthorized: Admin access required'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    class_id = data.get('class_id')
    date_of_birth_str = data.get('date_of_birth')
    parent_name = data.get('parent_name')
    parent_phone = data.get('parent_phone')


    if not all([username, password, first_name, last_name]):
        return jsonify({'message': 'Missing required fields (username, password, first_name, last_name)'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409

    if email and User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 409

    date_of_birth = None
    if date_of_birth_str:
        try:
            date_of_birth = date.fromisoformat(date_of_birth_str)
        except ValueError:
            return jsonify({'message': 'Invalid date_of_birth format. Use YYYY-MM-DD'}), 400

    try:
        new_user = User(
            username=username,
            role='student',
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush() # استخدم flush للحصول على new_user.id قبل commit النهائي

        existing_class = None
        if class_id:
            existing_class = Class.query.get(class_id)
            if not existing_class:
                db.session.rollback()
                return jsonify({'message': f'Class with ID {class_id} not found'}), 404

        new_student = Student(
            user_id=new_user.id,
            class_id=class_id,
            date_of_birth=date_of_birth,
            parent_name=parent_name,
            parent_phone=parent_phone
        )
        db.session.add(new_student)
        db.session.commit()

        return jsonify({'message': 'Student added successfully', 'student_id': new_student.id, 'user_id': new_user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred during student registration', 'error': str(e)}), 500

# جلب جميع الطلاب
@app.route('/api/students', methods=['GET'])
def get_all_students():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    students = Student.query.all()
    students_data = []
    for student in students:
        user_info = student.user
        class_name = student.class_obj.name if student.class_obj else 'غير محدد'

        students_data.append({
            'student_id': student.id,
            'user_id': user_info.id,
            'username': user_info.username,
            'first_name': user_info.first_name,
            'last_name': user_info.last_name,
            'email': user_info.email,
            'phone_number': user_info.phone_number,
            'class_id': student.class_id,
            'class_name': class_name,
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
            'parent_name': student.parent_name,
            'parent_phone': student.parent_phone
        })
    return jsonify(students_data), 200

# إضافة درجة (teacher أو admin)
@app.route('/api/grades', methods=['POST'])
def add_grade():
    if 'user_id' not in session or session.get('role') not in ['teacher', 'admin']:
        return jsonify({'message': 'Unauthorized: Teacher or Admin access required to add grades'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    student_id = data.get('student_id')
    subject_id = data.get('subject_id')
    assessment_type = data.get('assessment_type')
    score = data.get('score')
    max_score = data.get('max_score')
    date_str = data.get('date')

    teacher_user_id = session['user_id']
    teacher_profile = Teacher.query.filter_by(user_id=teacher_user_id).first()
    if not teacher_profile:
         return jsonify({'message': 'Authenticated teacher profile not found'}), 403

    if not all([student_id, subject_id, assessment_type, score, max_score]):
        return jsonify({'message': 'Missing required fields (student_id, subject_id, assessment_type, score, max_score)'}), 400

    student = Student.query.get(student_id)
    subject = Subject.query.get(subject_id)

    if not student:
        return jsonify({'message': f'Student with ID {student_id} not found'}), 404
    if not subject:
        return jsonify({'message': f'Subject with ID {subject_id} not found'}), 404

    grade_date = date.today()
    if date_str:
        try:
            grade_date = date.fromisoformat(date_str)
        except ValueError:
            return jsonify({'message': 'Invalid date format for grade. Use YYYY-MM-DD'}), 400

    try:
        new_grade = Grade(
            student_id=student.id,
            subject_id=subject.id,
            teacher_id=teacher_profile.id,
            assessment_type=assessment_type,
            score=score,
            max_score=max_score,
            date=grade_date
        )
        db.session.add(new_grade)
        db.session.commit()

        return jsonify({'message': 'Grade added successfully', 'grade_id': new_grade.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while adding grade', 'error': str(e)}), 500

# جلب درجات طالب معين
@app.route('/api/students/<int:student_id>/grades', methods=['GET'])
def get_student_grades(student_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'message': f'Student with ID {student_id} not found'}), 404

    current_user_role = session.get('role')
    current_user_id = session.get('user_id')

    # منطق الصلاحيات:
    if current_user_role == 'student' and student.user_id != current_user_id:
        return jsonify({'message': 'Forbidden: You can only view your own grades'}), 403
    
    # يمكن إضافة منطق أكثر تعقيداً هنا للمعلمين (مثلاً، المعلم يرى فقط درجات طلابه في مواده)
    # حالياً، إذا كان المستخدم معلماً أو مديراً، يسمح له بالرؤية
    if current_user_role not in ['student', 'teacher', 'admin']:
        return jsonify({'message': 'Forbidden: Invalid role for this action'}), 403

    grades = Grade.query.filter_by(student_id=student_id).all()
    grades_data = []
    for grade in grades:
        subject_name = grade.subject_obj.name if grade.subject_obj else 'N/A'
        teacher_name = f"{grade.teacher_obj.user.first_name} {grade.teacher_obj.user.last_name}" if grade.teacher_obj and grade.teacher_obj.user else 'N/A'

        grades_data.append({
            'grade_id': grade.id,
            'subject_name': subject_name,
            'assessment_type': grade.assessment_type,
            'score': grade.score,
            'max_score': grade.max_score,
            'percentage': (grade.score / grade.max_score * 100) if grade.max_score else 0,
            'date': grade.date.isoformat(),
            'teacher_name': teacher_name
        })
    return jsonify(grades_data), 200

# =========================================================
# API نقاط النهاية لإدارة الصفوف والمواد (جديد)
# =========================================================

# جلب جميع الصفوف
@app.route('/api/classes', methods=['GET'])
def get_classes():
    # يمكن السماح لأي مستخدم مسجل الدخول برؤية الصفوف
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    classes = Class.query.all()
    classes_data = []
    for cls in classes:
        classes_data.append({
            'id': cls.id,
            'name': cls.name,
            'year': cls.year
        })
    return jsonify(classes_data), 200

# إضافة صف جديد (admin فقط)
@app.route('/api/classes', methods=['POST'])
def add_class():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'message': 'Unauthorized: Admin access required'}), 401

    data = request.get_json()
    name = data.get('name')
    year = data.get('year')

    if not name:
        return jsonify({'message': 'Class name is required'}), 400
    
    if Class.query.filter_by(name=name).first():
        return jsonify({'message': 'Class with this name already exists'}), 409

    try:
        new_class = Class(name=name, year=year)
        db.session.add(new_class)
        db.session.commit()
        return jsonify({'message': 'Class added successfully', 'class_id': new_class.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while adding class', 'error': str(e)}), 500

# جلب جميع المواد
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    subjects = Subject.query.all()
    subjects_data = []
    for sub in subjects:
        subjects_data.append({
            'id': sub.id,
            'name': sub.name
        })
    return jsonify(subjects_data), 200

# إضافة مادة جديدة (admin فقط)
@app.route('/api/subjects', methods=['POST'])
def add_subject():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'message': 'Unauthorized: Admin access required'}), 401

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'message': 'Subject name is required'}), 400
    
    if Subject.query.filter_by(name=name).first():
        return jsonify({'message': 'Subject with this name already exists'}), 409

    try:
        new_subject = Subject(name=name)
        db.session.add(new_subject)
        db.session.commit()
        return jsonify({'message': 'Subject added successfully', 'subject_id': new_subject.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while adding subject', 'error': str(e)}), 500


# =========================================================
# API نقطة نهاية لجلب بيانات لوحة التحكم (Dashboards)
# =========================================================

@app.route('/api/dashboard/student', methods=['GET'])
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({'message': 'Unauthorized: Student access required'}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    student_profile = Student.query.filter_by(user_id=user_id).first()

    if not user or not student_profile:
        return jsonify({'message': 'Student profile not found'}), 404

    # جلب الدرجات
    grades_data = []
    for grade in student_profile.grades:
        subject_name = grade.subject_obj.name if grade.subject_obj else 'N/A'
        teacher_name = f"{grade.teacher_obj.user.first_name} {grade.teacher_obj.user.last_name}" if grade.teacher_obj and grade.teacher_obj.user else 'N/A'
        grades_data.append({
            'subject': subject_name,
            'assessment_type': grade.assessment_type,
            'score': grade.score,
            'max_score': grade.max_score,
            'date': grade.date.isoformat(),
            'teacher': teacher_name
        })

    # جلب سجل الحضور
    attendance_data = []
    for record in student_profile.attendance_records:
        subject_name = record.subject_obj.name if record.subject_obj else 'N/A'
        attendance_data.append({
            'date': record.date.isoformat(),
            'subject': subject_name,
            'status': record.status
        })
    
    # جلب الجدول الدراسي (افتراضي أو من قاعدة البيانات إذا كان لديك نموذج Schedule)
    # حالياً، لا يوجد نموذج Schedule مفصل، لذلك يمكننا إرجاع بيانات افتراضية أو تركها فارغة
    schedule_data = [] # يمكن ملؤها من قاعدة البيانات لاحقاً

    # جلب ملاحظات المعلمين (افتراضي أو من قاعدة البيانات إذا كان لديك نموذج Note)
    notes_data = [] # يمكن ملؤها من قاعدة البيانات لاحقاً

    return jsonify({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'class_name': student_profile.class_obj.name if student_profile.class_obj else 'غير محدد',
        'grades': grades_data,
        'attendance': attendance_data,
        'schedule': schedule_data,
        'notes': notes_data
    }), 200

@app.route('/api/dashboard/teacher', methods=['GET'])
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({'message': 'Unauthorized: Teacher access required'}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    teacher_profile = Teacher.query.filter_by(user_id=user_id).first()

    if not user or not teacher_profile:
        return jsonify({'message': 'Teacher profile not found'}), 404

    taught_subjects_names = [sub.name for sub in teacher_profile.taught_subjects]

    return jsonify({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'specialization': teacher_profile.specialization,
        'hire_date': teacher_profile.hire_date.isoformat() if teacher_profile.hire_date else None,
        'taught_subjects': taught_subjects_names
    }), 200

@app.route('/api/dashboard/admin', methods=['GET'])
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'message': 'Unauthorized: Admin access required'}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    admin_profile = Admin.query.filter_by(user_id=user_id).first()

    if not user or not admin_profile:
        return jsonify({'message': 'Admin profile not found'}), 404
    
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_classes = Class.query.count()
    total_users = User.query.count()

    return jsonify({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_users': total_users # يمكن إضافتها للوحة التحكم الإدارية
    }), 200


# =========================================================
# 4. نقطة الدخول لتشغيل التطبيق وإنشاء قاعدة البيانات وإضافة بيانات افتراضية
# =========================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # هذا سيقوم بإنشاء جميع الجداول أو التأكد من وجودها

        # إضافة بيانات افتراضية إذا كانت قاعدة البيانات فارغة
        if User.query.count() == 0:
            print("Adding initial data...")
            # مدير افتراضي
            admin_user = User(username='admin', role='admin', first_name='المدير', last_name='العام', email='admin@school.com')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            # ربط المدير بجدول Admin
            db.session.add(Admin(user_id=admin_user.id))
            db.session.commit()

            # معلم افتراضي
            teacher_user = User(username='teacher', role='teacher', first_name='أحمد', last_name='المعلم', email='teacher@school.com')
            teacher_user.set_password('teacher123')
            db.session.add(teacher_user)
            db.session.commit()
            # ربط المعلم بجدول Teacher
            teacher_profile = Teacher(user_id=teacher_user.id, specialization='الرياضيات', hire_date=date(2020, 9, 1))
            db.session.add(teacher_profile)
            db.session.commit()

            # صف افتراضي
            class_1a = Class(name='الصف العاشر أ', year=2025)
            db.session.add(class_1a)
            db.session.commit()

            # طالب افتراضي
            student_user = User(username='student', role='student', first_name='فاطمة', last_name='الطالبة', email='student@school.com')
            student_user.set_password('student123')
            db.session.add(student_user)
            db.session.commit()

            # ربط الطالب بالصف
            student_profile = Student(user_id=student_user.id, class_id=class_1a.id, date_of_birth=date(2008, 5, 15),
                                      parent_name='ولي أمر فاطمة', parent_phone='0501112233')
            db.session.add(student_profile)
            db.session.commit()

            # مادة افتراضية
            math_subject = Subject(name='الرياضيات')
            db.session.add(math_subject)
            db.session.commit()
            
            arabic_subject = Subject(name='اللغة العربية')
            db.session.add(arabic_subject)
            db.session.commit()

            # ربط المعلم بالمادة التي يدرسها (علاقة Many-to-Many)
            teacher_profile.taught_subjects.append(math_subject)
            db.session.commit()

            # ربط الصف بالمادة التي تدرس فيه (علاقة Many-to-Many)
            class_1a.subjects_taught_in_class.append(math_subject)
            db.session.commit()

            # إضافة درجة للطالب
            grade1 = Grade(student_id=student_profile.id, subject_id=math_subject.id, teacher_id=teacher_profile.id,
                           assessment_type='اختبار شهري', score=85.0, max_score=100.0)
            db.session.add(grade1)
            db.session.commit()

            # إضافة سجل حضور للطالب
            attendance1 = Attendance(student_id=student_profile.id, subject_id=math_subject.id, teacher_id=teacher_profile.id,
                                    date=date.today(), status='present')
            db.session.add(attendance1)
            db.session.commit()

            print("Initial data added successfully.")

        app.run(debug=True)