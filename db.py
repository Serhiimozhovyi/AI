"""Read-only helpers for talking to the course database."""

import pandas as pd
import psycopg2

from config import DATABASE_URL


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def run_query(sql: str) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql(sql, conn)


def get_course_completion_summary() -> pd.DataFrame:
    """One row per course: enrollments, completions, completion rate, avg progress."""
    sql = """
        SELECT
            dc.course,
            dc.domain,
            dc.level,
            COUNT(e.enrollment_id) AS enrollments,
            SUM(CASE WHEN e.completed_at IS NOT NULL THEN 1 ELSE 0 END) AS completed,
            ROUND(AVG(e.progress_pct)::numeric, 1) AS avg_progress,
            ROUND(
                100.0 * SUM(CASE WHEN e.completed_at IS NOT NULL THEN 1 ELSE 0 END)
                / NULLIF(COUNT(e.enrollment_id), 0),
                1
            ) AS completion_rate_pct
        FROM enrollments e
        JOIN dim_course dc ON dc.course_id = e.course_id
        GROUP BY dc.course, dc.domain, dc.level
        HAVING COUNT(e.enrollment_id) >= 20
        ORDER BY completion_rate_pct DESC NULLS LAST
    """
    return run_query(sql)


def get_most_popular_courses(limit: int = 10) -> pd.DataFrame:
    """Courses ranked by number of enrollments (what people actually sign up for most)."""
    sql = f"""
        SELECT
            dc.course,
            COUNT(e.enrollment_id) AS enrollments,
            ROUND(
                100.0 * SUM(CASE WHEN e.completed_at IS NOT NULL THEN 1 ELSE 0 END)
                / NULLIF(COUNT(e.enrollment_id), 0),
                1
            ) AS completion_rate_pct
        FROM enrollments e
        JOIN dim_course dc ON dc.course_id = e.course_id
        GROUP BY dc.course
        ORDER BY enrollments DESC
        LIMIT {int(limit)}
    """
    return run_query(sql)


def get_overall_metrics() -> dict:
    sql = """
        SELECT
            COUNT(*) AS total_enrollments,
            ROUND(AVG(progress_pct)::numeric, 1) AS avg_progress,
            SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS completed
        FROM enrollments
    """
    row = run_query(sql).iloc[0]
    return {
        "total_enrollments": int(row["total_enrollments"]),
        "avg_progress": float(row["avg_progress"]),
        "completed": int(row["completed"]),
    }


def get_funnel_breakdown() -> pd.DataFrame:
    """Enrollment funnel stage counts (registered -> viewed -> explored -> certified)."""
    sql = """
        SELECT funnel_state, COUNT(*) AS enrollments
        FROM enrollments
        GROUP BY funnel_state
        ORDER BY enrollments DESC
    """
    return run_query(sql)


def get_engagement_metrics() -> dict:
    sql = """
        SELECT
            ROUND(AVG(minutes_watched)::numeric, 1) AS avg_minutes_per_week,
            ROUND(AVG(quiz_score)::numeric, 1) AS avg_quiz_score,
            COUNT(DISTINCT enrollment_id) AS active_enrollments
        FROM weekly_activity
    """
    row = run_query(sql).iloc[0]
    return {
        "avg_minutes_per_week": float(row["avg_minutes_per_week"]),
        "avg_quiz_score": float(row["avg_quiz_score"]),
        "active_enrollments": int(row["active_enrollments"]),
    }


def get_revenue_metrics() -> dict:
    sql = """
        SELECT
            SUM(amount_usd) AS total_revenue,
            COUNT(*) AS total_payments,
            SUM(CASE WHEN is_refunded = 1 THEN 1 ELSE 0 END) AS refunds,
            ROUND(100.0 * SUM(CASE WHEN is_refunded = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS refund_rate_pct
        FROM payments
    """
    row = run_query(sql).iloc[0]
    return {
        "total_revenue": float(row["total_revenue"]),
        "total_payments": int(row["total_payments"]),
        "refunds": int(row["refunds"]),
        "refund_rate_pct": float(row["refund_rate_pct"]),
    }


def get_revenue_by_plan() -> pd.DataFrame:
    sql = """
        SELECT
            plan,
            COUNT(*) AS payments,
            SUM(amount_usd) AS revenue,
            ROUND(100.0 * SUM(CASE WHEN is_refunded = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS refund_rate_pct
        FROM payments
        GROUP BY plan
        ORDER BY revenue DESC
    """
    return run_query(sql)


def get_users_by_plan() -> pd.DataFrame:
    sql = "SELECT plan, COUNT(*) AS users FROM users GROUP BY plan ORDER BY users DESC"
    return run_query(sql)


def get_users_by_persona() -> pd.DataFrame:
    sql = "SELECT persona, COUNT(*) AS users FROM users GROUP BY persona ORDER BY users DESC"
    return run_query(sql)


def get_users_by_country(limit: int = 10) -> pd.DataFrame:
    sql = f"""
        SELECT country, COUNT(*) AS users
        FROM users
        GROUP BY country
        ORDER BY users DESC
        LIMIT {int(limit)}
    """
    return run_query(sql)


def get_signup_trend() -> pd.DataFrame:
    sql = """
        SELECT date_trunc('month', signup_date)::date AS month, COUNT(*) AS signups
        FROM users
        GROUP BY month
        ORDER BY month
    """
    return run_query(sql)


def get_review_metrics() -> dict:
    sql = "SELECT ROUND(AVG(stars)::numeric, 2) AS avg_stars, COUNT(*) AS total_reviews FROM reviews"
    row = run_query(sql).iloc[0]
    return {"avg_stars": float(row["avg_stars"]), "total_reviews": int(row["total_reviews"])}


def get_top_rated_specializations(limit: int = 10) -> pd.DataFrame:
    sql = f"""
        SELECT specialization_name, review_score, review_count
        FROM specializations
        WHERE review_score IS NOT NULL
        ORDER BY review_score DESC, review_count DESC
        LIMIT {int(limit)}
    """
    return run_query(sql)
