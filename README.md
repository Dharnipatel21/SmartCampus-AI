# SmartCampus AI

AI-Powered Smart Campus Management System

Full-stack university management system integrating real AI/ML features into academic workflows.

# Overview

SmartCampus AI digitalizes core campus operations including attendance tracking, marks management, outpass approvals, helpdesk tickets, and timetable management.

It integrates two practical AI components:

GPT-based academic assistant

Cosine Similarity based study resource recommender

The goal is to demonstrate meaningful AI integration in institutional systems, not just basic automation.

# Student Portal

Dashboard with attendance, exams, fees overview

Subject-wise attendance tracking with detention alerts

Internal, external marks and CGPA calculation

Timetable grid view

4-stage outpass approval workflow

On-duty request submission

Helpdesk ticket system

AI study resource recommendations

GPT-powered academic chatbot

# Teacher Portal

Multi-stage outpass approvals

On-duty approval system

Real-time availability status

Helpdesk ticket management

# AI Components
1. GPT Academic Assistant

Model: OpenAI GPT-3.5-turbo

Technique: Prompt engineering with database context injection

Uses live student academic data before generating responses

Maintains short conversation memory

Includes rule-based fallback if API key is not configured

2. Study Resource Recommender

Algorithm: Content-based filtering using Cosine Similarity

Input: Student marks and attendance

Output: Ranked study resources per subject

Uses feature vector comparison to match difficulty level

# Tech Stack

Backend: Python, Flask
Database: SQLite
Frontend: HTML, CSS, JavaScript
AI: OpenAI GPT-3.5-turbo
ML: Cosine Similarity (Content-Based Filtering)
Database

# 11 tables including:

students

teachers

attendance

marks

timetable

fees

outpass_requests

helpdesk_tickets

# API Sample Endpoints

POST /api/student/login

GET /api/attendance/:id

GET /api/marks/:id

POST /api/outpass/submit

GET /api/ai/recommendations/:id

POST /api/chatbot
