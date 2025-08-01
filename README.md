Got it. Here's a sharp, no-bloat **README draft** to lock your architecture, flow, and philosophy into words. This ain’t no brochure — this is your code’s **doctrine**.

---

# 📚 E-Learning API – Tutor & Student Modules (Open Marking System)

### 🧠 Philosophy

Knowledge is open. So is evaluation. This platform encourages collaborative learning through tutor-created content and **open-source assignment marking**.

---

## 🔐 Auth & Tokens

* JWT token is generated on registration/login.
* Token must be attached to **every protected route** via `Authorization` header (`Bearer <token>`).
* Backend uses `validate_token()` dependency to extract and confirm user identity.

---

## 🎓 Student Module

### 🚪 Register

```http
POST /student/register
```

Fields: `name`, `email`, `phone_number`, `password`

### 🔑 Login

```http
POST /student/login
```

Returns a token.

### 📝 Submit Assignment

```http
POST /student/doassignment
```

Requires token.
Fields: `course_id`, `exercise`, `lesson_title`, etc.

### 🧠 Take Quiz

```http
POST /student/takequiz
```

Same structure as assignment. Uses `wrk` query param (`quiz`, `assignment`).

### 🧾 View Results

```http
GET /student/viewresult?wrk=assignment
```

### 📦 View All Submissions

```http
GET /student/viewall?wrk=quiz
```

---

## 🧑‍🏫 Tutor Module

### 🚪 Register

```http
POST /tutor/register
```

### 🔑 Login

```http
POST /tutor/login
```

### 🧠 Give Quiz/Assignment

```http
POST /tutor/givequiz?wrk=quiz
```

Backend returns a `course_id`.
**Frontend must cache this like a token** and auto-insert it when students are submitting.

---

## 🛠 Admin Module

### 🚪 Register & Login

`/admin/register`, `/admin/login`

### 📘 Create Course

```http
POST /create/course
```

Backend auto-generates and returns a unique `course_id`.

---

## 🔁 Course ID Handling (Critical 🔒)

* `course_id` is generated **once** when a tutor/admin creates a course.
* **Frontend must cache it (like a JWT)**.
* Students never select it manually — it's auto-attached during submissions.
* This ensures traceability, consistency, and access control.

---

## 📣 Open Marking System

> **Any tutor can mark any assignment or quiz.**

* No marking lock-in.
* Promotes peer review.
* Rating and reputation systems (coming soon) will let better tutors rise.

---

## 🧃 Stack

* **FastAPI**
* **MongoDB Atlas**
* **Pydantic**
* **JWT Auth**
* **bcrypt for password security**

---

## 🚨 Future Upgrades

* Tutor/Student Rating System
* Lesson-level analytics
* Time-limited submissions
* Chat between tutor and students
* Auto-correction engine (AI-based)

---

## 💡 Final Note

This platform is built like a battlefield — **modular**, **scalable**, and **open**.
Code isn't just logic, it's leverage.

> *“When the student submits, the world learns.”*

---

Need a markdown version? Or want this pushed as `/docs` route on your API with Swagger or Redoc?
