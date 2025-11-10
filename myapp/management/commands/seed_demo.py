from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from myapp.models import Subject, Chapter, Topic, LectureSession, TopicProgress, Enrollment
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed MGMU (Aurangabad) B.Tech Integrated CSE (DS) – Semester 5: Java Programming syllabus with users, enrollments, chapters, topics, and sessions.'

    def handle(self, *args, **options):
        # --- Groups ---
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        student_group, _ = Group.objects.get_or_create(name='Student')

        # --- Users ---
        t, created = User.objects.get_or_create(
            username='alice_teacher',
            defaults={
                'email': 'alice@example.com',
                'first_name': 'Alice',
                'last_name': 'Johnson'
            }
        )
        if created:
            t.set_password('teacherpass')
            t.save()
            t.groups.add(teacher_group)

        students = [
            ('bob_student', 'Bob', 'Wilson'),
            ('carol_student', 'Carol', 'Smith'),
            ('dave_student', 'Dave', 'Brown'),
            ('eve_student', 'Eve', 'Davis'),
        ]
        for username, first, last in students:
            s, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': first,
                    'last_name': last,
                }
            )
            if created:
                s.set_password('studentpass')
                s.save()
                s.groups.add(student_group)

        # --- Subject (mapped from provided syllabus) ---
        # Teaching Hours (sum of units): 7 + 8 + 8 + 8 + 8 + 6 = 45
        start_date = timezone.now().date() - timedelta(days=30)
        subject_name = 'Java Programming'
        subj, _ = Subject.objects.get_or_create(
            name=subject_name,
            defaults={
                'class_name': 'B.Tech (Integrated) CSE (Data Science) – Sem 5',
                'planned_lectures': 45,
                'start_date': start_date,
            }
        )

        # Link teacher to subject via Enrollment (role='teacher')
        Enrollment.objects.get_or_create(user=t, subject=subj, defaults={'role': 'teacher'})

        # --- Chapters & Topics (Units → Chapters; bullet points → Topics) ---
        units = [
            (
                'Unit I: Basic Syntactical Constructs in Java',
                [
                    'Java features & programming environment',
                    'Defining classes and creating objects',
                    'Tokens, identifiers, and data types',
                    'Variables, scope, initialization & typecasting',
                    'Arrays and strings basics',
                    'Operators & expressions; precedence and evaluation',
                    'Control flow: if / if-else / switch / ?: operator',
                    'Loops: while, do-while, for, nested & labeled',
                    'Enhanced for-each loop',
                    'Math library: min, max, sqrt, pow, exp, round, abs',
                ],
            ),
            (
                'Unit II: Derived Syntactical Constructs in Java',
                [
                    'Constructors & methods; types and nesting of methods',
                    'Argument passing; the this keyword; varargs',
                    'Command-line arguments',
                    'Garbage collection & finalize(); java.lang.Object',
                    'Visibility control: public, private, protected, default',
                    'Arrays: 1D/2D creation & usage',
                    'Strings & StringBuffer classes',
                    'Collections intro: Vector; wrapper classes',
                    'Enumerated types (enum)',
                ],
            ),
            (
                'Unit III: Inheritance, Interfaces, and Packages',
                [
                    'Inheritance concepts & types: single, multilevel, hierarchical',
                    'Method & constructor overloading vs overriding',
                    'Dynamic method dispatch (runtime polymorphism)',
                    'final variables & methods; use of super; abstract classes',
                    'Static members and their use',
                    'Interfaces: defining, implementing, accessing members',
                    'Extending interfaces; interface references; nested interfaces',
                    'Packages: define, name, create, and access',
                    'Import & static import; adding classes/interfaces to packages',
                ],
            ),
            (
                'Unit IV: Exception Handling and Multithreading',
                [
                    'Errors vs exceptions; exception hierarchy',
                    'try/catch; nested try; throws; finally',
                    'Built-in exceptions',
                    'Custom exceptions; throw; chained exceptions',
                    'Creating threads: extends Thread vs implements Runnable',
                    'Thread lifecycle & key methods: wait, sleep, notify',
                    'Thread control: priority, resume/suspend/stop (legacy)',
                    'Synchronization & inter-thread communication',
                    'Deadlock patterns and avoidance',
                ],
            ),
            (
                'Unit V: Java Applets and Graphics Programming',
                [
                    'Applet basics & life cycle (skeleton)',
                    'Applet tag in HTML; passing parameters',
                    'Embedding <applet> in Java code; adding controls',
                    'Graphics class overview & drawing context',
                    'Drawing primitives: lines, rectangles, ellipses/circles, arcs, polygons',
                    'Colors & paint; setColor/getColor; foreground/background',
                    'Fonts: Font class (name, size, style)',
                    'Font methods: getFamily, getFont, getFontName, getSize, getStyle',
                    'GraphicsEnvironment: getAllFonts & available font family names',
                ],
            ),
            (
                'Unit VI: Managing Input/Output and Files in Java',
                [
                    'I/O streams concept and hierarchy',
                    'Byte streams: InputStream/OutputStream families',
                    'Character streams: Reader/Writer families',
                    'Using streams effectively (buffering, flushing, closing)',
                    'File class usage & file system operations',
                    'I/O exceptions & handling patterns',
                    'Creating files & directories',
                    'Reading/writing characters and bytes',
                    'Handling primitive data types (DataInput/DataOutput streams)',
                ],
            ),
        ]

        for chapter_idx, (chapter_title, topics) in enumerate(units, start=1):
            chapter, _ = Chapter.objects.get_or_create(
                subject=subj,
                title=chapter_title,
                order=chapter_idx,
            )
            for topic_idx, topic_title in enumerate(topics, start=1):
                topic, _ = Topic.objects.get_or_create(
                    chapter=chapter,
                    title=topic_title,
                    order=topic_idx,
                )
                # Seed progress to showcase dashboards
                for student in User.objects.filter(groups=student_group):
                    if chapter_idx <= 2:
                        status = 'completed'
                    elif chapter_idx == 3:
                        status = 'in_progress' if topic_idx <= 3 else 'not_started'
                    elif chapter_idx == 4:
                        status = 'in_progress' if topic_idx == 1 else 'not_started'
                    else:
                        status = 'not_started'
                    TopicProgress.objects.get_or_create(
                        student=student,
                        topic=topic,
                        defaults={'status': status},
                    )

        # --- Lecture Sessions (roughly one per teaching hour over time; here every 3 days) ---
        session_dates = [
            (start_date + timedelta(days=i), f'Java Lecture {i // 3 + 1}')
            for i in range(0, 45, 3)
        ]
        for date, title in session_dates:
            if date <= timezone.now().date():
                attendees = 25 + (date.day % 10)  # 25–34 attendees
                LectureSession.objects.get_or_create(
                    subject=subj,
                    date=date,
                    defaults={
                        'attendees': attendees,
                        'notes': f'{title}: Covered scheduled topics; engagement was good.',
                    },
                )

        self.stdout.write(self.style.SUCCESS(
            'Java Programming syllabus seeded. Teacher: alice_teacher/teacherpass, Student: bob_student/studentpass'
        ))
