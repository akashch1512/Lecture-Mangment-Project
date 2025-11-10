from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from myapp.models import Subject, Chapter, Topic, LectureSession, TopicProgress, Enrollment
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed Principles of Modern Cryptography (theory + lab) with users, enrollments, chapters, topics, progress, and sessions.'

    def handle(self, *args, **options):
        # --- Groups ---
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        student_group, _ = Group.objects.get_or_create(name='Student')

        # --- Users (same pattern as your example) ---
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

        # Dates & counts
        start_date = timezone.now().date() - timedelta(days=30)  # same approach as your seed
        planned_lectures_theory = 6 + 8 + 8 + 8 + 8 + 7  # = 45
        planned_lectures_lab = 11 * 2  # 11 practicals × 2 hours = 22

        # --- Subject: Theory ---
        theory_name = 'Principles of Modern Cryptography'
        theory_subj, _ = Subject.objects.get_or_create(
            name=theory_name,
            defaults={
                'class_name': 'B.Tech (Integrated) CSE – Semester',
                'planned_lectures': planned_lectures_theory,
                'start_date': start_date,
            }
        )
        Enrollment.objects.get_or_create(user=t, subject=theory_subj, defaults={'role': 'teacher'})

        # Units -> (Chapter title, [topics...])
        theory_units = [
            (
                'Unit I: Introduction to Cryptography and Classical Cryptosystems (6 Hrs)',
                [
                    'Overview of Cryptography: History and evolution; importance in modern digital communication; terminology (plaintext, ciphertext, keys, encryption, decryption).',
                    'Classical Cryptographic Systems: Substitution (Caesar, monoalphabetic) and transposition ciphers; cryptanalysis of classical systems.',
                    'Basic Security Goals.',
                ],
            ),
            (
                'Unit II: Block Ciphers and Symmetric Key Cryptography (8 Hrs)',
                [
                    'Block Ciphers: Principles and modes of operation; key length and security implications; DES and its vulnerabilities.',
                    'Advanced Symmetric Ciphers: AES design, key sizes, modes of operation; strengths and weaknesses of symmetric-key encryption.',
                    'Cryptographic Attacks on Symmetric Systems: Brute-force, differential, linear cryptanalysis; birthday paradox; meet-in-the-middle.',
                ],
            ),
            (
                'Unit III: Public-Key Cryptography and RSA Algorithm (8 Hrs)',
                [
                    'Asymmetric Basics: Public/private keys; key exchange problem; Diffie–Hellman key exchange.',
                    'RSA Algorithm: Primes, modular arithmetic, Euler’s theorem; RSA encryption/decryption; security and attacks (factoring, timing, chosen-ciphertext).',
                    'Digital Signatures: Principles; RSA for signatures and authentication.',
                ],
            ),
            (
                'Unit IV: Cryptographic Hash Functions and Message Authentication (8 Hrs)',
                [
                    'Hash Functions: Definition and properties; MD5, SHA-1, SHA-256; applications (integrity, fingerprinting, password hashing).',
                    'Message Authentication Codes (MACs): Purpose and design; HMAC and its security; MACs vs digital signatures.',
                    'Applications: Authentication, integrity checking, digital certificates.',
                ],
            ),
            (
                'Unit V: Key Management and Public Key Infrastructure (PKI) (8 Hrs)',
                [
                    'Key Management: Generation, distribution, storage; symmetric vs asymmetric management; DH and ECDH.',
                    'Public Key Infrastructure: Certificates, CAs, CRLs; X.509; trust models and certificate validation.',
                    'PKI in Practice: SSL/TLS, email encryption (PGP, S/MIME), VPNs.',
                ],
            ),
            (
                'Unit VI: Advanced Cryptographic Techniques and Modern Protocols (7 Hrs)',
                [
                    'Elliptic Curve Cryptography (ECC): Basics and elliptic curve cryptosystems.',
                    'Zero-Knowledge Proofs: Introduction and applications.',
                    'Post-Quantum Cryptography: Quantum threats to classical crypto.',
                    'Cryptographic Protocols: SSL/TLS handshake; Bitcoin and blockchain-based cryptography.',
                    'Privacy-Preserving Protocols: Homomorphic encryption; private set intersection.',
                ],
            ),
        ]

        for chapter_idx, (chapter_title, topics) in enumerate(theory_units, start=1):
            chapter, _ = Chapter.objects.get_or_create(
                subject=theory_subj,
                title=chapter_title,
                order=chapter_idx,
            )
            for topic_idx, topic_title in enumerate(topics, start=1):
                topic, _ = Topic.objects.get_or_create(
                    chapter=chapter,
                    title=topic_title,
                    order=topic_idx,
                )
                # Seed progress like your example
                for student in User.objects.filter(groups=student_group):
                    if chapter_idx <= 2:
                        status = 'completed'
                    elif chapter_idx == 3:
                        status = 'in_progress' if topic_idx <= 2 else 'not_started'
                    elif chapter_idx == 4:
                        status = 'in_progress' if topic_idx == 1 else 'not_started'
                    else:
                        status = 'not_started'
                    TopicProgress.objects.get_or_create(
                        student=student,
                        topic=topic,
                        defaults={'status': status},
                    )

        # Lecture Sessions for theory (every 3 days, like your Java seed)
        theory_session_dates = [
            (start_date + timedelta(days=i), f'Crypto Lecture {i // 3 + 1}')
            for i in range(0, planned_lectures_theory, 3)
        ]
        for date, title in theory_session_dates:
            if date <= timezone.now().date():
                attendees = 25 + (date.day % 10)  # 25–34 attendees
                LectureSession.objects.get_or_create(
                    subject=theory_subj,
                    date=date,
                    defaults={
                        'attendees': attendees,
                        'notes': f'{title}: Covered scheduled topics; engagement was good.',
                    },
                )

        # --- Subject: Lab ---
        lab_name = 'Principles of Modern Cryptography Lab'
        lab_subj, _ = Subject.objects.get_or_create(
            name=lab_name,
            defaults={
                'class_name': 'B.Tech (Integrated) CSE – Semester',
                'planned_lectures': planned_lectures_lab,
                'start_date': start_date,
            }
        )
        Enrollment.objects.get_or_create(user=t, subject=lab_subj, defaults={'role': 'teacher'})

        # Single chapter with all practicals as topics (order preserved)
        lab_chapter, _ = Chapter.objects.get_or_create(
            subject=lab_subj,
            title='Lab Experiments',
            order=1,
        )
        lab_practicals = [
            'Study different techniques in symmetric key cryptography.',
            'Implementing Caesar Cipher.',
            'Implementing Vigenère Cipher.',
            'Symmetric Key Encryption with DES (Data Encryption Standard).',
            'Symmetric Key Encryption with AES (Advanced Encryption Standard).',
            'Implementing RSA Public Key Cryptosystem.',
            'Case Study: Security of Real-World Cryptographic Protocol.',
            'Implementing Hash Functions (MD5 and SHA-256).',
            'RSA Digital Signature Process.',
            'Study Elliptic Curve Cryptography.',
            'Case Study: Homomorphic Encryption.',
        ]
        for idx, title in enumerate(lab_practicals, start=1):
            topic, _ = Topic.objects.get_or_create(
                chapter=lab_chapter,
                title=title,
                order=idx,
            )
            # Lab progress: first 3 completed, next 3 in progress, rest not started
            for student in User.objects.filter(groups=student_group):
                if idx <= 3:
                    status = 'completed'
                elif idx <= 6:
                    status = 'in_progress'
                else:
                    status = 'not_started'
                TopicProgress.objects.get_or_create(
                    student=student,
                    topic=topic,
                    defaults={'status': status},
                )

        # Lab sessions (one per practical, weekly)
        lab_session_dates = [
            (start_date + timedelta(days=7 * (i - 1)), f'Crypto Lab {i}')
            for i in range(1, len(lab_practicals) + 1)
        ]
        for date, title in lab_session_dates:
            if date <= timezone.now().date():
                attendees = 20 + (date.day % 8)  # 20–27 attendees
                LectureSession.objects.get_or_create(
                    subject=lab_subj,
                    date=date,
                    defaults={
                        'attendees': attendees,
                        'notes': f'{title}: Completed scheduled experiment.',
                    },
                )

        # Enroll students to both subjects
        for student in User.objects.filter(groups=student_group):
            Enrollment.objects.get_or_create(user=student, subject=theory_subj, defaults={'role': 'student'})
            Enrollment.objects.get_or_create(user=student, subject=lab_subj, defaults={'role': 'student'})

        self.stdout.write(self.style.SUCCESS(
            'Seeded: Principles of Modern Cryptography (theory + lab). '
            'Teacher: alice_teacher/teacherpass, Students: bob_student|carol_student|dave_student|eve_student (pw: studentpass)'
        ))
