Below is the **complete revised Project Draft** with the **Dean/HOD role completely removed**. The system now has only **Admin, Teacher, and Student** roles.

---

# Project Draft: Institutional Online Examination, Coding Assessment & Practice Platform

## 1. Project Title

**Institutional Online Examination and Coding Assessment System**

*(Alternative names: Smart Exam Portal / EduExam Pro)*

---

# 2. Overview

A role-based web platform that allows educational institutions (schools, colleges, or individual teachers) to conduct MCQ-based examinations (similar to IndiaBix), programming/coding assessments (similar to LeetCode/HackerRank), and self-paced practice sessions.

The system supports three user roles—**Admin, Teacher, and Student**—enabling secure creation and distribution of formal examinations using unique exam codes, flexible practice sets for skill development, automated evaluation, and comprehensive performance analytics.

Formal examinations and practice sessions are maintained separately so that practice performance never affects official examination grades.

---

# 3. Problem Statement

Traditional examination systems (paper-based or basic online platforms) suffer from several limitations:

* Lack of centralized management for both MCQ and coding questions.
* Limited support for practical programming skill evaluation.
* Weak security during online examinations.
* No structured practice environment before official exams.
* Limited analytics for student progress.
* Manual grading for programming assignments.
* Difficulty in monitoring examination integrity.
* Lack of automated reporting for teachers and administrators.

---

# 4. Objectives

* Allow teachers to create and manage MCQ and coding question banks.
* Allow students to register, join classes, and attend examinations using unique exam codes.
* Provide an online coding editor with instant execution and test-case evaluation.
* Allow teachers to create standalone practice sets that students can attempt anytime without exam codes.
* Allow teachers to monitor student progress separately for practice and examinations.
* Allow administrators to monitor institutional activity, student performance, and platform usage.
* Provide automatic grading for MCQs and coding questions.
* Implement examination security features such as timers, tab-switch detection, auto submission, and copy-paste detection.

---

# 5. Scope of the Project

## In Scope

* User registration and role-based login (Admin, Teacher, Student)
* Institution → Class → Student management
* MCQ Question Bank
* Coding Question Bank
* Two working modes:

### Exam Mode

* Unique exam code
* Timed examination
* Limited attempts
* Randomized questions
* Anti-cheating features
* Official grading

### Practice Mode

* No exam code
* Unlimited attempts
* Immediate feedback
* Optional explanations
* Self-paced learning

Additional features include:

* Mixed exams containing MCQs and coding questions
* Practice set creation
* Browser-based code editor
* Sandboxed code execution
* Automatic grading
* Student progress tracking
* Performance analytics
* Reports for teachers and administrators

---

## Out of Scope

* Multi-institution SaaS platform
* Webcam proctoring
* Mobile applications
* AI-generated questions
* Essay evaluation
* Support for all programming languages

Initially supported languages:

* Python
* C++
* Java

---

# 6. User Roles & Responsibilities

## Admin

* Manage the entire platform
* Create teacher accounts
* Manage students and classes
* Manage system settings
* View institution-wide reports
* Monitor examinations
* Monitor practice activities
* Generate overall analytics

---

## Teacher

* Create MCQ question banks
* Create coding problems
* Create examinations
* Generate exam codes
* Create practice sets
* Schedule examinations
* Monitor ongoing exams
* View student submissions
* Evaluate performance reports
* Analyze practice statistics

---

## Student

* Register and login
* Join assigned class
* Attend examinations using exam codes
* Attempt practice sets
* Solve coding problems
* View examination results
* Track practice progress
* Review previous attempts

---

# 7. Core Features

## A. General Features

### Authentication

* Secure login
* Role-based dashboards

### Class Management

* Institution
* Classes
* Students

### Question Bank

Supports:

* MCQs
* Coding Questions

Each question stores:

* Marks
* Difficulty
* Topic
* Tags

### Exam Creation

Teachers can configure:

* Duration
* Schedule
* Randomization
* Mixed question types
* Exam codes

### Examination Monitoring

* Timer
* Tab switch detection
* Copy-paste detection
* Auto submission

### Automatic Grading

* Instant MCQ grading
* Coding evaluation using hidden test cases

### Reporting

Reports include:

* Student performance
* Class performance
* Subject-wise analysis
* Practice analytics

---

# B. Coding Assessment Module

## Coding Question Bank

Stores:

* Title
* Description
* Difficulty
* Input format
* Output format
* Sample test cases
* Hidden test cases
* Starter code
* Time limits
* Memory limits
* Topic tags

---

## Online Code Editor

Features:

* Language selector
* Syntax highlighting
* Run button
* Submit button
* Output console

---

## Judge Engine

Supports:

* Secure sandbox execution
* Hidden test cases
* Runtime error detection
* Compilation error detection
* Time limit exceeded detection
* Partial marking

---

## Mixed Examination

Single examination containing:

* MCQs
* Coding questions

Combined score generated automatically.

---

## Coding Anti-Cheating

Exam mode only:

* Copy-paste detection
* Activity logging
* Future plagiarism detection

---

## Coding Analytics

Teachers can view:

* Pass rate
* Failure reasons
* Student solve statistics
* Topic-wise difficulty

---

# C. Practice Module

## Practice Set Creation

Teachers create:

* MCQ-only sets
* Coding-only sets
* Mixed sets

Assign directly to classes.

---

## Open Access

Students can:

* View available practice sets
* Start immediately
* No exam code required

---

## Unlimited Practice

Students may:

* Retry unlimited times
* Learn at their own pace
* Receive immediate feedback

---

## Solutions and Explanations

Teachers may enable:

* Correct MCQ explanation
* Coding reference solution

Displayed after:

* First attempt
* Selected number of attempts

---

## Practice Monitoring

### Student Analytics

* Questions attempted
* Completion percentage
* Average attempts
* Time spent
* Learning streak

---

### Question Analytics

* Attempt count
* Success rate
* Common wrong answers
* Common coding failures

---

### Topic Analytics

Identify:

* Weak topics
* Strong topics
* Frequently skipped topics

---

### Improvement Trends

Track:

* Weekly progress
* Monthly progress
* Success rate changes

---

## Teacher Dashboard

Displays:

* Student engagement
* Practice heatmap
* Weak topic alerts
* Leaderboards
* Progress reports

---

## Student Dashboard

Displays:

* Practice progress
* Completed topics
* Statistics
* Recommended practice questions
* Future AI recommendations

---

# 8. Assumptions & Constraints

* Initial version supports only one institution.
* Supports Python, C++, and Java initially.
* Secure sandbox required for code execution.
* Practice attempts remain separate from examination attempts.
* Teachers may use the platform independently.
* Internet connection required during examinations.
* Coding evaluation is output-based only.

---

# 9. Expected Outcome

A secure web-based examination and coding assessment platform where teachers can independently create and conduct formal examinations and publish flexible practice sets. Students can participate in official examinations using unique exam codes while also improving their skills through unlimited self-paced practice sessions.

The system provides automated grading, examination monitoring, coding evaluation, performance analytics, and comprehensive dashboards for teachers and administrators. It is designed to improve learning outcomes while reducing manual effort in conducting and evaluating examinations.


