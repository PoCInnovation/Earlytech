use axum::{routing::{get, post, delete}, Router};
use crate::handlers::{
    add_excluded_keyword,
    add_excluded_source,
    add_user_keyword,
    delete_excluded_keyword,
    delete_excluded_source,
    delete_user_keyword,
    get_article,
    get_article_count,
    get_delivery_stats,
    get_recent_deliveries,
    get_user_exclusions,
    get_user_feed,
    get_user_preferences,
    get_user_quality_stats,
    get_user_stats,
    list_articles,
    list_user_keywords,
    login_user_handler,
    register_user_handler,
    update_user_preferences,
    upsert_user_feedback,
};
use crate::state::AppState;

pub fn create_router(state: AppState) -> Router {
    Router::new()
        .route("/", get(|| async { "API Root" }))
        // Articles
        .route("/articles/count", get(get_article_count))
        .route("/articles", get(list_articles))
        .route("/articles/:id", get(get_article))
        // Auth
        .route("/auth/register", post(register_user_handler))
        .route("/auth/login", post(login_user_handler))
        // User keywords
        .route("/users/:id/keywords", get(list_user_keywords))
        .route("/users/:id/keywords", post(add_user_keyword))
        .route("/users/:user_id/keywords/:keyword_id", delete(delete_user_keyword))
        // User preferences (digest)
        .route("/users/:id/preferences", get(get_user_preferences))
        .route("/users/:id/preferences", post(update_user_preferences))
        // User exclusions (sources + keywords)
        .route("/users/:id/exclusions", get(get_user_exclusions))
        .route("/users/:id/exclusions/sources", post(add_excluded_source))
        .route("/users/:user_id/exclusions/sources/:source", delete(delete_excluded_source))
        .route("/users/:id/exclusions/keywords", post(add_excluded_keyword))
        .route("/users/:user_id/exclusions/keywords/:keyword_id", delete(delete_excluded_keyword))
        // User feedback + quality dashboard
        .route("/users/:id/feedback", post(upsert_user_feedback))
        .route("/users/:id/quality", get(get_user_quality_stats))
        // User feed & stats
        .route("/users/:id/feed", get(get_user_feed))
        .route("/users/:id/stats", get(get_user_stats))
        // Global delivery stats
        .route("/delivery/stats", get(get_delivery_stats))
        .route("/delivery/recent", get(get_recent_deliveries))
        .with_state(state)
}
