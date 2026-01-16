# Job Application Tracker - Frontend API Documentation

> **Complete API Reference for Frontend Development**  
> Base URL: `http://localhost:8000/api/v1/`  
> API Documentation: `http://localhost:8000/api/docs/` (Swagger UI)

---

## Table of Contents

1. [Authentication & Authorization](#1-authentication--authorization)
2. [User Management](#2-user-management)
3. [Companies](#3-companies)
4. [Applications](#4-applications)
5. [Interviews](#5-interviews)
6. [Analytics & Dashboard](#6-analytics--dashboard)
7. [AI Features](#7-ai-features)
8. [Notifications](#8-notifications)
9. [Two-Factor Authentication](#9-two-factor-authentication)
10. [Webhooks](#10-webhooks)
11. [Exports](#11-exports)
12. [Health Checks](#12-health-checks)
13. [Data Models & Types](#13-data-models--types)
14. [Error Handling](#14-error-handling)
15. [Rate Limiting](#15-rate-limiting)

---

## 1. Authentication & Authorization

### Authentication Method
- **Type**: JWT (JSON Web Tokens)
- **Header**: `Authorization: Bearer <access_token>`
- **Access Token Lifetime**: 60 minutes
- **Refresh Token Lifetime**: 7 days

### Endpoints

#### Register New User
```
POST /api/v1/auth/register/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "",
    "linkedin_url": "",
    "portfolio_url": "",
    "github_url": "",
    "desired_role": "",
    "desired_salary_min": null,
    "desired_salary_max": null,
    "preferred_work_type": "any",
    "is_email_verified": false,
    "created_at": "2026-01-16T10:00:00Z",
    "updated_at": "2026-01-16T10:00:00Z"
  },
  "tokens": {
    "refresh": "eyJ...",
    "access": "eyJ..."
  },
  "message": "Registration successful. Please check your email to verify your account."
}
```

---

#### Login
```
POST /api/v1/auth/login/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "refresh": "eyJ...",
  "access": "eyJ..."
}
```

---

#### Refresh Token
```
POST /api/v1/auth/token/refresh/
```

**Request Body:**
```json
{
  "refresh": "eyJ..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

---

#### Logout
```
POST /api/v1/auth/logout/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "refresh": "eyJ..."
}
```

**Response (200 OK):**
```json
{
  "message": "Logout successful."
}
```

---

#### Verify Email
```
POST /api/v1/auth/verify-email/
```

**Request Body:**
```json
{
  "token": "verification_token_from_email"
}
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully. Welcome!"
}
```

---

#### Resend Verification Email
```
POST /api/v1/auth/resend-verification/
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "If an account exists with this email, a verification link has been sent."
}
```

---

#### Request Password Reset
```
POST /api/v1/auth/password-reset/
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "If an account exists with this email, a password reset link has been sent."
}
```

---

#### Confirm Password Reset
```
POST /api/v1/auth/password-reset/confirm/
```

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePass123!",
  "new_password_confirm": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password has been reset successfully. You can now log in with your new password."
}
```

---

## 2. User Management

### Get/Update Profile
```
GET /api/v1/auth/profile/
PUT /api/v1/auth/profile/
PATCH /api/v1/auth/profile/
```
**Auth Required**: Yes

**Response/Request Body:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "portfolio_url": "https://johndoe.dev",
  "github_url": "https://github.com/johndoe",
  "desired_role": "Full Stack Developer",
  "desired_salary_min": 80000,
  "desired_salary_max": 120000,
  "preferred_work_type": "remote",
  "is_email_verified": true,
  "created_at": "2026-01-16T10:00:00Z",
  "updated_at": "2026-01-16T10:00:00Z"
}
```

**Work Type Options:**
- `remote` - Remote
- `hybrid` - Hybrid
- `onsite` - On-site
- `any` - Any

---

### Change Password
```
PUT /api/v1/auth/change-password/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "old_password": "CurrentPassword123!",
  "new_password": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password updated successfully."
}
```

---

## 3. Companies

### List Companies
```
GET /api/v1/companies/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by name, industry, location |
| `size` | string | Filter by company size |
| `industry` | string | Filter by industry |
| `ordering` | string | Order by: `name`, `created_at`, `glassdoor_rating` |
| `page` | integer | Page number |

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/companies/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Google",
      "industry": "Technology",
      "location": "Mountain View, CA",
      "application_count": 3
    }
  ]
}
```

---

### Create Company
```
POST /api/v1/companies/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "name": "Google",
  "website": "https://google.com",
  "industry": "Technology",
  "location": "Mountain View, CA",
  "size": "enterprise",
  "glassdoor_rating": 4.5,
  "notes": "Great company culture"
}
```

**Company Size Options:**
- `startup` - Startup (1-50)
- `small` - Small (51-200)
- `medium` - Medium (201-1000)
- `large` - Large (1001-5000)
- `enterprise` - Enterprise (5000+)

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Google",
  "website": "https://google.com",
  "industry": "Technology",
  "location": "Mountain View, CA",
  "size": "enterprise",
  "glassdoor_rating": "4.5",
  "notes": "Great company culture",
  "application_count": 0,
  "created_at": "2026-01-16T10:00:00Z",
  "updated_at": "2026-01-16T10:00:00Z"
}
```

---

### Get/Update/Delete Company
```
GET /api/v1/companies/{id}/
PUT /api/v1/companies/{id}/
PATCH /api/v1/companies/{id}/
DELETE /api/v1/companies/{id}/
```
**Auth Required**: Yes

---

## 4. Applications

### List Applications
```
GET /api/v1/applications/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by job title, company name, location |
| `status` | string | Filter by status |
| `priority` | string | Filter by priority |
| `work_type` | string | Filter by work type |
| `source` | string | Filter by source |
| `company` | integer | Filter by company ID |
| `ordering` | string | Order by: `applied_date`, `updated_at`, `created_at`, `priority`, `status` |
| `page` | integer | Page number |

**Response (200 OK):**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/v1/applications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "company": 1,
      "company_name": "Google",
      "job_title": "Senior Software Engineer",
      "status": "interviewing",
      "priority": "high",
      "work_type": "hybrid",
      "location": "Mountain View, CA",
      "source": "linkedin",
      "applied_date": "2026-01-10",
      "days_since_applied": 6,
      "updated_at": "2026-01-16T10:00:00Z"
    }
  ]
}
```

---

### Create Application
```
POST /api/v1/applications/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "company": 1,
  "job_title": "Senior Software Engineer",
  "job_url": "https://careers.google.com/jobs/123",
  "job_description": "We are looking for...",
  "status": "applied",
  "priority": "high",
  "work_type": "hybrid",
  "location": "Mountain View, CA",
  "salary_min": 150000,
  "salary_max": 200000,
  "source": "linkedin",
  "referrer_name": "",
  "cover_letter": "Dear Hiring Manager...",
  "resume_version": 1,
  "applied_date": "2026-01-10",
  "next_action": "Follow up email",
  "next_action_date": "2026-01-20"
}
```

**Status Options:**
- `wishlist` - Wishlist
- `applied` - Applied
- `screening` - Screening
- `interviewing` - Interviewing
- `offer` - Offer Received
- `accepted` - Accepted
- `rejected` - Rejected
- `withdrawn` - Withdrawn
- `ghosted` - Ghosted

**Priority Options:**
- `high` - High
- `medium` - Medium
- `low` - Low

**Work Type Options:**
- `remote` - Remote
- `hybrid` - Hybrid
- `onsite` - On-site

**Source Options:**
- `linkedin` - LinkedIn
- `indeed` - Indeed
- `glassdoor` - Glassdoor
- `company_site` - Company Website
- `referral` - Referral
- `recruiter` - Recruiter
- `job_fair` - Job Fair
- `other` - Other

---

### Get Application Detail
```
GET /api/v1/applications/{id}/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "id": 1,
  "company": 1,
  "company_name": "Google",
  "company_details": {
    "id": 1,
    "name": "Google",
    "industry": "Technology",
    "location": "Mountain View, CA",
    "application_count": 3
  },
  "job_title": "Senior Software Engineer",
  "job_url": "https://careers.google.com/jobs/123",
  "job_description": "We are looking for...",
  "status": "interviewing",
  "priority": "high",
  "work_type": "hybrid",
  "location": "Mountain View, CA",
  "salary_min": 150000,
  "salary_max": 200000,
  "source": "linkedin",
  "referrer_name": "",
  "cover_letter": "Dear Hiring Manager...",
  "resume_version": 1,
  "applied_date": "2026-01-10",
  "response_date": "2026-01-13",
  "next_action": "Prepare for technical interview",
  "next_action_date": "2026-01-20",
  "days_since_applied": 6,
  "has_response": true,
  "notes_count": 3,
  "interviews_count": 2,
  "notes": [
    {
      "id": 1,
      "content": "Had a great initial call",
      "note_type": "general",
      "created_at": "2026-01-13T10:00:00Z",
      "updated_at": "2026-01-13T10:00:00Z"
    }
  ],
  "created_at": "2026-01-10T10:00:00Z",
  "updated_at": "2026-01-16T10:00:00Z"
}
```

---

### Update Application Status (Quick Update)
```
PATCH /api/v1/applications/{id}/status/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "status": "interviewing",
  "response_date": "2026-01-13"
}
```

---

### Application Notes
```
GET /api/v1/applications/{id}/notes/
POST /api/v1/applications/{id}/notes/
```
**Auth Required**: Yes

**Create Note Request Body:**
```json
{
  "content": "Great phone screen with the hiring manager",
  "note_type": "general"
}
```

**Note Type Options:**
- `general` - General
- `follow_up` - Follow Up
- `feedback` - Feedback
- `research` - Company Research
- `preparation` - Interview Prep

---

### Resume Management

#### List Resumes
```
GET /api/v1/applications/resumes/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "version_name": "Backend Focus",
      "file_url": "https://res.cloudinary.com/...",
      "file_name": "john_doe_backend_resume.pdf",
      "file_size": 125000,
      "file_size_display": "122.1 KB",
      "cloudinary_public_id": "resumes/user_1/...",
      "is_default": true,
      "created_at": "2026-01-10T10:00:00Z"
    }
  ]
}
```

---

#### Upload Resume
```
POST /api/v1/applications/resumes/upload/
```
**Auth Required**: Yes  
**Content-Type**: `multipart/form-data`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | PDF or Word document (max 5MB) |
| `version_name` | string | Yes | Name for this version |
| `is_default` | boolean | No | Set as default resume |

**Allowed File Types:**
- `application/pdf`
- `application/msword`
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

---

#### Set Default Resume
```
POST /api/v1/applications/resumes/{id}/set-default/
```
**Auth Required**: Yes

---

#### Delete Resume
```
DELETE /api/v1/applications/resumes/{id}/
```
**Auth Required**: Yes

---

## 5. Interviews

### List Interviews
```
GET /api/v1/interviews/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by job title, company name, interviewer |
| `status` | string | Filter by status |
| `outcome` | string | Filter by outcome |
| `interview_type` | string | Filter by interview type |
| `application` | integer | Filter by application ID |
| `ordering` | string | Order by: `scheduled_at`, `created_at`, `round_number` |
| `page` | integer | Page number |

**Response (200 OK):**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "company_name": "Google",
      "job_title": "Senior Software Engineer",
      "round_number": 1,
      "interview_type": "phone",
      "scheduled_at": "2026-01-20T14:00:00Z",
      "duration_minutes": 45,
      "status": "scheduled",
      "outcome": "pending",
      "is_upcoming": true
    }
  ]
}
```

---

### Create Interview
```
POST /api/v1/interviews/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "application": 1,
  "round_number": 1,
  "interview_type": "phone",
  "scheduled_at": "2026-01-20T14:00:00Z",
  "duration_minutes": 45,
  "timezone": "America/Los_Angeles",
  "meeting_link": "https://meet.google.com/abc-defg-hij",
  "meeting_location": "",
  "interviewer_names": "Jane Smith, Bob Johnson",
  "interviewer_titles": "Engineering Manager, Senior Engineer",
  "status": "scheduled",
  "preparation_notes": "Review system design concepts"
}
```

**Interview Type Options:**
- `phone` - Phone Screen
- `technical` - Technical
- `behavioral` - Behavioral
- `coding` - Coding Challenge
- `system_design` - System Design
- `onsite` - On-site
- `hr` - HR/Final
- `other` - Other

**Status Options:**
- `scheduled` - Scheduled
- `completed` - Completed
- `cancelled` - Cancelled
- `rescheduled` - Rescheduled
- `no_show` - No Show

**Outcome Options:**
- `pending` - Pending
- `passed` - Passed
- `failed` - Failed

---

### Get Interview Detail
```
GET /api/v1/interviews/{id}/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "id": 1,
  "application": 1,
  "company_name": "Google",
  "job_title": "Senior Software Engineer",
  "round_number": 1,
  "interview_type": "phone",
  "scheduled_at": "2026-01-20T14:00:00Z",
  "duration_minutes": 45,
  "timezone": "America/Los_Angeles",
  "meeting_link": "https://meet.google.com/abc-defg-hij",
  "meeting_location": "",
  "interviewer_names": "Jane Smith",
  "interviewer_titles": "Engineering Manager",
  "status": "scheduled",
  "outcome": "pending",
  "preparation_notes": "Review system design concepts",
  "post_interview_notes": "",
  "questions_asked": "",
  "is_upcoming": true,
  "created_at": "2026-01-16T10:00:00Z",
  "updated_at": "2026-01-16T10:00:00Z"
}
```

---

### Update Interview Outcome
```
PATCH /api/v1/interviews/{id}/outcome/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "status": "completed",
  "outcome": "passed",
  "post_interview_notes": "Went well, discussed system design for a chat application"
}
```

---

### Get Upcoming Interviews
```
GET /api/v1/interviews/upcoming/
```
**Auth Required**: Yes

---

### Get Today's Interviews
```
GET /api/v1/interviews/today/
```
**Auth Required**: Yes

---

## 6. Analytics & Dashboard

### Dashboard Overview
```
GET /api/v1/analytics/dashboard/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "total_applications": 50,
  "active_applications": 35,
  "offers_received": 2,
  "interviews_scheduled": 5,
  "response_rate": 45.5,
  "avg_response_days": 7.2,
  "status_breakdown": {
    "applied": 15,
    "screening": 8,
    "interviewing": 10,
    "offer": 2,
    "rejected": 10,
    "ghosted": 5
  }
}
```

---

### Response Rate by Source
```
GET /api/v1/analytics/response-rate/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "by_source": [
    {
      "source": "referral",
      "total": 5,
      "with_response": 4,
      "response_rate": 80.0
    },
    {
      "source": "linkedin",
      "total": 20,
      "with_response": 8,
      "response_rate": 40.0
    }
  ]
}
```

---

### Application Funnel
```
GET /api/v1/analytics/funnel/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "funnel": [
    {"stage": "applied", "count": 50, "percentage": 100.0},
    {"stage": "screening", "count": 30, "percentage": 60.0},
    {"stage": "interviewing", "count": 15, "percentage": 30.0},
    {"stage": "offer", "count": 3, "percentage": 6.0},
    {"stage": "accepted", "count": 1, "percentage": 2.0}
  ],
  "total_applications": 50
}
```

---

### Weekly Activity
```
GET /api/v1/analytics/weekly/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `weeks` | integer | 12 | Number of weeks to include |

**Response (200 OK):**
```json
{
  "weekly_applications": [
    {"week": "2026-01-06T00:00:00Z", "count": 8},
    {"week": "2026-01-13T00:00:00Z", "count": 5}
  ],
  "period_weeks": 12
}
```

---

### Top Companies
```
GET /api/v1/analytics/top-companies/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Number of companies to return |

**Response (200 OK):**
```json
{
  "top_companies": [
    {
      "company__id": 1,
      "company__name": "Google",
      "application_count": 5,
      "interview_count": 3
    }
  ]
}
```

---

## 7. AI Features

### Generate Cover Letter
```
POST /api/v1/ai/cover-letter/generate/
```
**Auth Required**: Yes  
**Rate Limit**: 20 requests/hour

**Request Body:**
```json
{
  "job_description": "We are looking for a Senior Software Engineer...",
  "resume_text": "John Doe\nSoftware Engineer with 5 years...",
  "resume_version_id": 1,
  "company_name": "Google",
  "job_title": "Senior Software Engineer",
  "tone": "professional",
  "application_id": 1,
  "save_to_history": true,
  "async_mode": false
}
```

**Tone Options:**
- `professional` - Professional (default)
- `enthusiastic` - Enthusiastic
- `formal` - Formal
- `conversational` - Conversational

**Note:** Provide either `resume_text` OR `resume_version_id`, not both.

**Synchronous Response (200 OK):**
```json
{
  "cover_letter": "Dear Hiring Manager,\n\nI am writing to express...",
  "model": "llama-3.1-70b-versatile",
  "tokens_used": 1500,
  "saved_id": 123
}
```

**Asynchronous Response (202 Accepted):**
```json
{
  "task_id": 456,
  "status": "pending",
  "message": "Cover letter generation queued. Poll /api/v1/ai/tasks/{task_id}/ for status."
}
```

---

### Analyze Job Match
```
POST /api/v1/ai/job-match/analyze/
```
**Auth Required**: Yes  
**Rate Limit**: 20 requests/hour

**Request Body:**
```json
{
  "job_description": "Required: 5+ years experience in Python...",
  "resume_text": "John Doe\nSoftware Engineer...",
  "resume_version_id": 1,
  "application_id": 1,
  "save_to_history": true,
  "async_mode": false
}
```

**Response (200 OK):**
```json
{
  "analysis": {
    "match_score": 85,
    "matching_skills": ["Python", "Django", "PostgreSQL"],
    "missing_skills": ["Kubernetes"],
    "recommendations": ["Consider getting Kubernetes certification"],
    "summary": "Strong match for this position..."
  },
  "model": "llama-3.1-70b-versatile",
  "tokens_used": 1200,
  "saved_id": 124
}
```

---

### Generate Interview Questions
```
POST /api/v1/ai/interview-questions/generate/
```
**Auth Required**: Yes  
**Rate Limit**: 20 requests/hour

**Request Body:**
```json
{
  "job_description": "We are looking for a Senior Software Engineer...",
  "company_name": "Google",
  "job_title": "Senior Software Engineer",
  "question_count": 10,
  "application_id": 1,
  "save_to_history": true,
  "async_mode": false
}
```

**Response (200 OK):**
```json
{
  "questions": "1. Tell me about a time when you had to...\n2. How would you design a...",
  "model": "llama-3.1-70b-versatile",
  "tokens_used": 800,
  "saved_id": 125
}
```

---

### AI Task Status (for async operations)
```
GET /api/v1/ai/tasks/{task_id}/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "id": 456,
  "task_type": "cover_letter",
  "task_type_display": "Cover Letter",
  "status": "completed",
  "status_display": "Completed",
  "input_params": {
    "company_name": "Google",
    "job_title": "Senior Software Engineer",
    "tone": "professional"
  },
  "result": {
    "cover_letter": "Dear Hiring Manager...",
    "model": "llama-3.1-70b-versatile",
    "tokens_used": 1500
  },
  "error_message": "",
  "created_at": "2026-01-16T10:00:00Z",
  "started_at": "2026-01-16T10:00:01Z",
  "completed_at": "2026-01-16T10:00:05Z",
  "duration": 4.0
}
```

**Task Status Options:**
- `pending` - Pending
- `processing` - Processing
- `completed` - Completed
- `failed` - Failed

---

### List AI Tasks
```
GET /api/v1/ai/tasks/
```
**Auth Required**: Yes

---

### AI Generation History
```
GET /api/v1/ai/history/
GET /api/v1/ai/history/{id}/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "count": 25,
  "results": [
    {
      "id": 123,
      "content_type": "cover_letter",
      "content_type_display": "Cover Letter",
      "input_company_name": "Google",
      "input_job_title": "Senior Software Engineer",
      "output_content": "Dear Hiring Manager...",
      "model_used": "llama-3.1-70b-versatile",
      "tokens_used": 1500,
      "is_favorite": false,
      "rating": null,
      "created_at": "2026-01-16T10:00:00Z"
    }
  ]
}
```

---

### Update AI History Item (favorite/rating)
```
PATCH /api/v1/ai/history/{id}/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "is_favorite": true,
  "rating": 5
}
```

---

## 8. Notifications

### Get/Update Notification Preferences
```
GET /api/v1/notifications/preferences/
PUT /api/v1/notifications/preferences/
PATCH /api/v1/notifications/preferences/
```
**Auth Required**: Yes

**Response/Request Body:**
```json
{
  "interview_reminders": true,
  "interview_reminder_hours": 24,
  "application_updates": true,
  "weekly_summary": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00"
}
```

---

### Notification History
```
GET /api/v1/notifications/history/
GET /api/v1/notifications/history/{id}/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_type` | string | Filter by type |

**Response (200 OK):**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "notification_type": "interview_reminder",
      "notification_type_display": "Interview Reminder",
      "subject": "Interview Tomorrow: Google - Senior Software Engineer",
      "status": "sent",
      "status_display": "Sent",
      "sent_at": "2026-01-15T10:00:00Z",
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

**Notification Types:**
- `interview_reminder` - Interview Reminder
- `application_status` - Application Status Change
- `weekly_summary` - Weekly Summary
- `custom` - Custom Notification

---

## 9. Two-Factor Authentication

### Get 2FA Status
```
GET /api/v1/2fa/status/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "enabled": false,
  "verified": false,
  "verified_at": null,
  "last_used_at": null,
  "backup_codes_remaining": 0
}
```

---

### Setup 2FA
```
POST /api/v1/2fa/setup/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgo...",
  "backup_codes": [
    "ABCD-1234",
    "EFGH-5678",
    "IJKL-9012"
  ],
  "otpauth_url": "otpauth://totp/Job%20Application%20Tracker:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Job%20Application%20Tracker",
  "message": "Scan the QR code with your authenticator app, then confirm with a code."
}
```

---

### Confirm 2FA Setup
```
POST /api/v1/2fa/confirm/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "2FA has been enabled for your account.",
  "enabled": true
}
```

---

### Verify 2FA Code
```
POST /api/v1/2fa/verify/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "verified": true,
  "method": "totp"
}
```

Or with backup code:
```json
{
  "verified": true,
  "method": "backup_code",
  "warning": "Backup code used. Consider regenerating your backup codes."
}
```

---

### Disable 2FA
```
POST /api/v1/2fa/disable/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "code": "123456",
  "password": "CurrentPassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "2FA has been disabled for your account.",
  "enabled": false
}
```

---

### Regenerate Backup Codes
```
POST /api/v1/2fa/backup-codes/regenerate/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "backup_codes": [
    "WXYZ-1234",
    "QRST-5678",
    "MNOP-9012"
  ],
  "message": "Backup codes regenerated. Save these securely."
}
```

---

## 10. Webhooks

### List Webhook Endpoints
```
GET /api/v1/webhooks/endpoints/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "count": 2,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My Integration",
      "url": "https://myapp.com/webhook",
      "secret": "abc123...",
      "events": ["application.created", "application.status_changed"],
      "is_active": true,
      "failure_count": 0,
      "last_failure_at": null,
      "last_success_at": "2026-01-16T10:00:00Z",
      "created_at": "2026-01-10T10:00:00Z",
      "updated_at": "2026-01-16T10:00:00Z",
      "delivery_stats": {
        "total_24h": 10,
        "successful_24h": 10,
        "failed_24h": 0
      }
    }
  ]
}
```

---

### Create Webhook Endpoint
```
POST /api/v1/webhooks/endpoints/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "name": "My Integration",
  "url": "https://myapp.com/webhook",
  "events": ["application.created", "application.status_changed"],
  "is_active": true
}
```

**Available Events:**
- `application.created` - Application Created
- `application.updated` - Application Updated
- `application.deleted` - Application Deleted
- `application.status_changed` - Application Status Changed
- `interview.created` - Interview Created
- `interview.updated` - Interview Updated
- `interview.completed` - Interview Completed
- `interview.cancelled` - Interview Cancelled
- `company.created` - Company Created

---

### Get Available Events
```
GET /api/v1/webhooks/endpoints/events/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "events": [
    {"name": "application.created", "description": "Application Created"},
    {"name": "application.updated", "description": "Application Updated"}
  ]
}
```

---

### Test Webhook
```
POST /api/v1/webhooks/endpoints/{id}/test/
```
**Auth Required**: Yes

**Request Body:**
```json
{
  "event": "application.created"
}
```

---

### Regenerate Webhook Secret
```
POST /api/v1/webhooks/endpoints/{id}/regenerate_secret/
```
**Auth Required**: Yes

**Response (200 OK):**
```json
{
  "message": "Secret regenerated successfully",
  "secret": "new_secret_here..."
}
```

---

### Webhook Deliveries
```
GET /api/v1/webhooks/deliveries/
GET /api/v1/webhooks/deliveries/{id}/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `endpoint` | uuid | Filter by endpoint ID |
| `status` | string | Filter by status (pending, success, failed, retrying) |
| `event` | string | Filter by event type |

**Response (200 OK):**
```json
{
  "count": 100,
  "results": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "endpoint": "550e8400-e29b-41d4-a716-446655440000",
      "endpoint_name": "My Integration",
      "event": "application.created",
      "payload": {
        "event": "application.created",
        "data": { "id": 1, "job_title": "..." }
      },
      "status": "success",
      "attempt_count": 1,
      "max_attempts": 3,
      "response_status_code": 200,
      "error_message": "",
      "created_at": "2026-01-16T10:00:00Z",
      "delivered_at": "2026-01-16T10:00:01Z"
    }
  ]
}
```

---

### Retry Failed Delivery
```
POST /api/v1/webhooks/deliveries/{id}/retry/
```
**Auth Required**: Yes

---

## 11. Exports

### Export Applications (CSV)
```
GET /api/v1/exports/applications/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |

**Response**: CSV file download

---

### Export Companies (CSV)
```
GET /api/v1/exports/companies/
```
**Auth Required**: Yes

**Response**: CSV file download

---

### Export Interviews (CSV)
```
GET /api/v1/exports/interviews/
```
**Auth Required**: Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |

**Response**: CSV file download

---

### Export Full Report (ZIP)
```
GET /api/v1/exports/full-report/
```
**Auth Required**: Yes

**Response**: ZIP file containing all CSVs and summary

---

## 12. Health Checks

### Health Check (Full)
```
GET /api/v1/analytics/health/
```
**Auth Required**: No

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected"
}
```

**Status Values:**
- `healthy` - All systems operational
- `degraded` - Some non-critical systems unavailable (e.g., cache)
- `unhealthy` - Critical systems unavailable (e.g., database)

---

### Readiness Check
```
GET /api/v1/analytics/ready/
```
**Auth Required**: No

**Response (200 OK):**
```json
{
  "ready": true
}
```

---

### Liveness Check
```
GET /api/v1/analytics/live/
```
**Auth Required**: No

**Response (200 OK):**
```json
{
  "alive": true
}
```

---

## 13. Data Models & Types

### User Model
```typescript
interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  phone: string;
  linkedin_url: string;
  portfolio_url: string;
  github_url: string;
  desired_role: string;
  desired_salary_min: number | null;
  desired_salary_max: number | null;
  preferred_work_type: 'remote' | 'hybrid' | 'onsite' | 'any';
  is_email_verified: boolean;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}
```

### Company Model
```typescript
interface Company {
  id: number;
  name: string;
  website: string;
  industry: string;
  location: string;
  size: 'startup' | 'small' | 'medium' | 'large' | 'enterprise' | '';
  glassdoor_rating: number | null;
  notes: string;
  application_count: number;
  created_at: string;
  updated_at: string;
}
```

### Application Model
```typescript
interface Application {
  id: number;
  company: number;
  company_name: string;
  job_title: string;
  job_url: string;
  job_description: string;
  status: 'wishlist' | 'applied' | 'screening' | 'interviewing' | 'offer' | 'accepted' | 'rejected' | 'withdrawn' | 'ghosted';
  priority: 'high' | 'medium' | 'low';
  work_type: 'remote' | 'hybrid' | 'onsite' | '';
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  source: 'linkedin' | 'indeed' | 'glassdoor' | 'company_site' | 'referral' | 'recruiter' | 'job_fair' | 'other';
  referrer_name: string;
  cover_letter: string;
  resume_version: number | null;
  applied_date: string | null; // YYYY-MM-DD
  response_date: string | null; // YYYY-MM-DD
  next_action: string;
  next_action_date: string | null; // YYYY-MM-DD
  days_since_applied: number | null;
  has_response: boolean;
  notes_count: number;
  interviews_count: number;
  created_at: string;
  updated_at: string;
}
```

### Interview Model
```typescript
interface Interview {
  id: number;
  application: number;
  company_name: string;
  job_title: string;
  round_number: number;
  interview_type: 'phone' | 'technical' | 'behavioral' | 'coding' | 'system_design' | 'onsite' | 'hr' | 'other';
  scheduled_at: string; // ISO 8601
  duration_minutes: number;
  timezone: string;
  meeting_link: string;
  meeting_location: string;
  interviewer_names: string;
  interviewer_titles: string;
  status: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled' | 'no_show';
  outcome: 'pending' | 'passed' | 'failed';
  preparation_notes: string;
  post_interview_notes: string;
  questions_asked: string;
  is_upcoming: boolean;
  created_at: string;
  updated_at: string;
}
```

### Note Model
```typescript
interface Note {
  id: number;
  content: string;
  note_type: 'general' | 'follow_up' | 'feedback' | 'research' | 'preparation';
  created_at: string;
  updated_at: string;
}
```

### Resume Model
```typescript
interface ResumeVersion {
  id: number;
  version_name: string;
  file_url: string;
  file_name: string;
  file_size: number;
  file_size_display: string;
  cloudinary_public_id: string;
  is_default: boolean;
  created_at: string;
}
```

---

## 14. Error Handling

### Error Response Format
```json
{
  "error": "Error message here"
}
```

Or for validation errors:
```json
{
  "field_name": ["Error message 1", "Error message 2"],
  "another_field": ["Error message"]
}
```

### Common HTTP Status Codes
| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (for async operations) |
| 204 | No Content (for successful DELETE) |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## 15. Rate Limiting

### Default Limits
- **Anonymous requests**: 100/hour
- **Authenticated requests**: 1000/hour
- **AI generation endpoints**: 20/hour

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642345678
```

### Rate Limit Error Response (429)
```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

---

## API Documentation URLs

| URL | Description |
|-----|-------------|
| `/api/docs/` | Swagger UI Documentation |
| `/api/redoc/` | ReDoc Documentation |
| `/api/schema/` | OpenAPI 3.0 Schema (JSON) |

---

## Frontend Environment Variables

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# OAuth (if implementing social login later)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id

# Feature Flags
NEXT_PUBLIC_ENABLE_2FA=true
NEXT_PUBLIC_ENABLE_AI_FEATURES=true
NEXT_PUBLIC_ENABLE_WEBHOOKS=true
```

---

## Pagination

All list endpoints return paginated responses:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/applications/?page=2",
  "previous": null,
  "results": [...]
}
```

**Default page size**: 20 items

---

## Authentication Flow

1. **Register** → POST `/api/v1/auth/register/`
2. **Verify Email** (optional but recommended) → POST `/api/v1/auth/verify-email/`
3. **Login** → POST `/api/v1/auth/login/`
4. **Use Access Token** in `Authorization: Bearer <token>` header
5. **Refresh Token** when access token expires → POST `/api/v1/auth/token/refresh/`
6. **Logout** → POST `/api/v1/auth/logout/`

### With 2FA Enabled
1. **Login** → Returns tokens but with `requires_2fa: true`
2. **Verify 2FA** → POST `/api/v1/2fa/verify/`
3. Continue with normal flow

---

## Webhook Payload Format

```json
{
  "event": "application.status_changed",
  "timestamp": "2026-01-16T10:00:00Z",
  "data": {
    "id": 1,
    "job_title": "Senior Software Engineer",
    "company_name": "Google",
    "old_status": "applied",
    "new_status": "interviewing"
  }
}
```

### Webhook Signature Verification
```
X-Webhook-Signature: sha256=<HMAC-SHA256 of payload using secret>
```

---

## Recommended Frontend Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **State Management**: Zustand or TanStack Query
- **UI Library**: shadcn/ui + Tailwind CSS
- **Forms**: React Hook Form + Zod
- **HTTP Client**: Axios or fetch with custom wrapper
- **Charts**: Recharts or Chart.js
- **Date Handling**: date-fns
- **Icons**: Lucide React

---

*Generated on: January 16, 2026*
