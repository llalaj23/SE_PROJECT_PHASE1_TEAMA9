# Again & Again — Project Implementation Plan
## Albanian Second-Hand Marketplace

---

## The Project in One Sentence

A web-based marketplace where Albanian citizens can buy, sell, message, rate, and report second-hand items — built with Django, PostgreSQL, and Bootstrap 5.

---

## The Team

| Name | Role | Responsibility |
|---|---|---|
| Ledio Lalaj | Team Leader | Project setup, authentication, deployment, integration |
| Andrea Shtjefni | Backend | All view logic, APIs, item CRUD, messaging, offers, reports |
| Jeta Okshtuni | Database | All models, migrations, search, filtering, queries |
| Briana Vathi | Frontend | All HTML templates, CSS, JavaScript, UI/UX |

---

## How the Layers Work Together

```
[ Briana  ]  →  HTML pages the user sees in the browser
[ Andrea  ]  →  Python logic that runs when buttons are clicked
[ Jeta    ]  →  Database tables that store all the data
[ Ledio   ]  →  The foundation: project setup, login, deployment
```

Ledio builds the foundation first. Jeta builds the database second.
Andrea and Briana work in parallel after Sprint 1 is complete.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.11 | Team's chosen language |
| Web Framework | Django 5.x | Batteries-included, great for beginners |
| Database | PostgreSQL 16 | Required for full-text search features |
| Frontend | Django Templates + Bootstrap 5 | No Node.js or React needed |
| CSS | Bootstrap 5 (CDN) | Pre-built components, responsive by default |
| Icons | Bootstrap Icons (CDN) | Free, consistent icon set |
| Maps | Leaflet.js (CDN) | Free maps using OpenStreetMap, no API key needed |
| Image Gallery | Swiper.js + GLightbox (CDN) | Touch-friendly slider + fullscreen zoom |
| Deployment | Railway.app | Free credits, auto-deploy from GitHub, PostgreSQL included |

---

## Packages to Install

| Package | Purpose |
|---|---|
| django | The web framework |
| psycopg2-binary | Lets Django talk to PostgreSQL |
| django-allauth | Email login, verification, password reset |
| django-environ | Reads secrets from a .env file |
| Pillow | Required for image uploads |
| django-filter | Filter listings by category, price, city |
| django-crispy-forms + crispy-bootstrap5 | Makes Django forms look like Bootstrap 5 |
| django-simple-history | Logs every edit made to a listing (fraud audit) |
| django-encrypted-model-fields | Encrypts the Albanian national ID in the database |
| django-ratelimit | Prevents brute-force attacks on login |
| whitenoise | Serves static files (CSS/JS) in production |
| gunicorn | Production web server for Railway |

---
users/                    ← Ledio's app: login, register, profile
marketplace/              ← Andrea + Jeta's app: items, messages, offers, etc.

templates/
    base.html             ← Shared layout (navbar, footer) — Briana builds this first
    account/              ← Login, signup, password reset pages
    marketplace/          ← Item list, item detail, create, edit, chat pages
    users/                ← Profile pages
    admin_dashboard/      ← Admin moderation panel

static/
    css/main.css          ← Custom styles on top of Bootstrap
    js/utils.js           ← Shared JavaScript helpers
    js/polling.js         ← Notification badge updater (runs on every page)

media/                    ← Uploaded images (gitignored, never committed)
.env                      ← Secret keys and passwords (gitignored, never committed)
requirements.txt          ← List of all installed packages
Procfile                  ← Tells Railway how to start the server
PLAN.md                   ← This file
```

---

## Database Tables (What Gets Stored)

| Table | Stores | Key Fields |
|---|---|---|
| users | All registered accounts | email, full_name, national_id (encrypted), city, lat/lng, profile_picture |
| user_blocks | Who has blocked who | blocker, blocked |
| categories | Item categories (Clothing, Electronics, etc.) | name, slug, parent (for subcategories) |
| items | All listings for sale | seller, category, title, price, condition, status, city, lat/lng, is_deleted, search_vector |
| item_images | Photos for each listing | item, image file path, is_primary |
| item_edit_logs | History of every change to a listing | item, what changed, old value, new value |
| messages | Chat messages between users | sender, recipient, item context, body, is_read |
| offers | Price negotiation between buyer and seller | item, buyer, seller, offered_price, status, parent_offer |
| reviews | Post-transaction ratings | reviewer, reviewed_user, item, rating (1-5), comment |
| wishlists | Items a user has saved/favorited | user, item |
| notifications | In-app alerts | user, type, message, is_read |
| reports | Complaints submitted by users | reporter, reported_user, reported_item, reason, status |
| ban_suspensions | Admin moderation actions | user, type (warning/suspension/ban), ends_at |

**Soft Delete Rule:** Items are NEVER permanently deleted from the database. Instead, `is_deleted` is set to True and the item is hidden from users. This preserves history for messages, reviews, and fraud audits.

**Offer Chain:** Each offer links to the previous one via `parent_offer`. This creates a full negotiation history: Buyer offers → Seller counters → Buyer counters → Seller accepts.

---

## Features List (What the App Can Do)

### Authentication
- Register with email and password
- Verify email before accessing the platform
- Log in / log out
- Reset forgotten password via email link
- Albanian national ID stored securely (encrypted)

### Browsing & Search
- Home page shows recent listings in a card grid
- Search bar with full-text search (title + description)
- Filter by: category, price range, condition, city
- Sort by: newest, oldest, price low-to-high, price high-to-low
- Category icons on home page for quick browsing
- Paginated results (12 items per page)

### Item Listings
- Create a listing with title, description, price, category, condition, photos
- Upload multiple photos per listing
- Edit a listing (all edits are logged)
- Mark an item as sold
- Delete a listing (soft delete — hidden but not permanently removed)
- View full listing detail page with image gallery, map, and seller info

### Messaging
- Open a chat from any listing page
- Send and receive messages between buyer and seller
- New messages appear without refreshing the page (polling every 2.5 seconds)
- Unread message count shown on the chat icon

### Offers & Negotiation
- Buyer makes an offer with a custom price
- Seller can accept, reject, or counter with a different price
- Both sides can go back and forth
- Full offer history is saved and viewable
- Accepted offer marks the item as sold automatically

### Wishlist
- Click the heart icon on any listing to save it
- View all saved items on your profile's Wishlist tab
- Remove items from wishlist

### Reviews & Ratings
- After a transaction is completed, both parties can rate each other (1-5 stars)
- Optional written comment with the rating
- Average rating shown on every user's profile
- Only one review allowed per transaction

### User Profiles
- View any user's public profile
- See their active listings, reviews received, and rating average
- Edit your own profile: name, phone, city, profile photo

### Notifications
- Bell icon in navbar with unread count badge
- Badge updates automatically every 10 seconds without page reload
- Notifications for: new message, offer received, offer accepted, item sold, new review
- Mark all as read button

### Safety Features
- Report a user or listing with a description and optional screenshot
- Block a user — their listings disappear and messaging is disabled
- Unblock a user at any time
- Admins can view reports, ban users, suspend users, remove listings
- Edit history logged on all listings for fraud detection

### Location
- Items show approximate location on a map (Leaflet.js, free, no API key)
- Users can set their city for proximity-based browsing
- Location stored as latitude/longitude coordinates

---

## Sprint Plan (10 Weeks)

### Sprint 1 — Foundation (Week 1-2)
**Goal: The project runs, users can register and log in**

What gets built:
- Django project created and connected to PostgreSQL
- CustomUser model (email login, national ID, city, profile picture)
- Email registration with verification
- Password reset via email
- Base HTML template with navbar
- Category fixture data loaded into database

Who does what:
- Ledio: Project creation, settings, CustomUser model, allauth configuration
- Jeta: Write all models, run migrations, load category fixtures
- Briana: base.html, login page, register page
- Andrea: URL routing structure, placeholder views

Sprint 1 is done when: A new user can register, receive a verification email, click the link, and log in.

---

### Sprint 2 — Core Marketplace (Week 3-4)
**Goal: Users can post and browse listings**

What gets built:
- Item creation form with multi-image upload
- Item list (home/browse page) with card grid
- Item detail page with image gallery, condition badge, price, seller info
- Item edit and soft-delete
- Edit history logging
- Full-text search (PostgreSQL tsvector trigger and GIN index)
- Filter sidebar (category, price, condition, city)
- Pagination

Who does what:
- Ledio: Integration, URL wiring, code review
- Jeta: PostgreSQL full-text search setup, performance indexes, filter queryset
- Briana: Home page grid, item detail page, Swiper.js gallery, filter sidebar UI
- Andrea: Item CRUD views, image upload handler, search view

Sprint 2 is done when: A logged-in user can post a listing with photos, and another user can find it using the search bar.

---

### Sprint 3 — Social Features (Week 5-6)
**Goal: Users can communicate and interact**

What gets built:
- Messaging: send, receive, conversation list, chat window with polling
- Wishlist heart button (AJAX toggle)
- Offers: make offer, counter, accept, reject
- Notifications: Django signals create notifications automatically
- Notification badge in navbar updates every 10 seconds
- User profile page with tabs (listings, wishlist, reviews)

Who does what:
- Ledio: Django signals for notifications, security middleware
- Jeta: Message, Offer, Wishlist, Notification queries and indexes
- Briana: Chat UI with polling JS, wishlist heart button, notification badge, profile tabs
- Andrea: Messaging views, wishlist toggle endpoint, offer views, notification endpoint

Sprint 3 is done when: User A can message User B, make an offer, and both get notifications.

---

### Sprint 4 — Trust & Safety (Week 7-8)
**Goal: Users can rate, report, and block each other**

What gets built:
- Review submission (post-transaction, one per transaction)
- Star rating display on profiles with average
- Report form with optional screenshot upload
- Block/unblock users
- Blocked user filtering in listings and messaging
- Admin dashboard (view reports, ban/suspend users, remove listings)
- Leaflet map on item detail page

Who does what:
- Ledio: Admin panel, ban/suspend logic, middleware
- Jeta: Review, Report, Block queries, rating average calculation
- Briana: Report form, star display, admin dashboard, Leaflet map embed
- Andrea: Review view, report view, block/unblock views, admin actions

Sprint 4 is done when: A user can report another user, an admin can see the report and take action.

---

### Sprint 5 — Polish & Deployment (Week 9-10)
**Goal: The app is live and secure**

What gets built:
- Security hardening: rate limiting on login, HTTPS settings, encrypted national ID
- Whitenoise for static file serving
- Production settings file (DEBUG=False, HTTPS headers, secure cookies)
- Deploy to Railway.app with auto-deploy from GitHub
- Environment variables configured on Railway
- Responsive design testing on mobile
- Custom 404 and 500 error pages
- Final bug fixes and end-to-end testing

Who does what:
- Ledio: Deployment, Railway setup, production settings, security audit
- Jeta: Final migration checks, database backup strategy, query optimization
- Briana: Mobile responsive fixes, error pages, final UI polish
- Andrea: End-to-end testing, bug fixes, edge case handling

Sprint 5 is done when: The app is live at a Railway URL, works on mobile, and new users can register and use all features.

---

## How Each Key Feature Works (No Code)

### Authentication Flow
1. User visits the register page and fills in name, email, password
2. System sends a verification email with a link
3. User clicks the link — account is activated
4. User logs in with email and password
5. If password forgotten — request reset link, receive email, set new password
6. National ID is stored encrypted so even a database leak cannot expose it

### How Search Works
1. When a listing is saved, PostgreSQL automatically builds a search index from the title and description (using a database trigger)
2. When a user types in the search bar, PostgreSQL searches that pre-built index
3. Results are ranked by relevance (title matches rank higher than description matches)
4. Django-filter applies additional filters (category, price range, condition) on top of the search results
5. Results are paginated 12 per page

### How Messaging Works (No WebSockets)
1. User A opens a chat with User B about an item
2. User A types a message and clicks Send
3. JavaScript intercepts the form submit, sends it to the server without reloading the page
4. Every 2.5 seconds, JavaScript asks the server: "Any new messages since the last one I received?"
5. If yes, new messages are added to the chat window
6. This creates a real-time feel without needing complex WebSocket technology

### How Notifications Work
1. When a message is sent, an offer is made, or a review is left — Django signals automatically create a Notification record
2. A small JavaScript snippet on every page asks the server every 10 seconds: "How many unread notifications does this user have?"
3. The badge number in the navbar updates accordingly
4. Clicking the bell shows the notification list

### How the Offer Chain Works
1. Buyer makes an offer of 3000 Lek
2. Seller counters with 3500 Lek (the original offer is marked as "countered", a new offer is created)
3. Buyer counters with 3200 Lek (same process)
4. Seller accepts — the item is marked as sold, all other pending offers on the item are rejected, both users get a notification

---

## Ledio's Responsibility Summary

**Phase 1 (Week 1):** Create Django project, virtual environment, connect to PostgreSQL, create the CustomUser model, install and configure allauth for email login, create base.html and URL structure

**Phase 2 (Week 2):** Configure email settings, test email verification flow, set up .env secrets file

**Phase 3 (Ongoing):** Review teammates' pull requests, handle integration issues when features are combined

**Phase 4 (Week 9-10):** Deploy to Railway.app, set production environment variables, configure HTTPS, create production settings

---

## Jeta's Responsibility Summary

**Phase 1 (Week 1):** Install PostgreSQL, create database, write ALL Django models, run initial migrations, load category fixture data

**Phase 2 (Week 2):** Set up PostgreSQL full-text search (tsvector column, GIN index, database trigger), create django-filter FilterSet for the browse page

**Phase 3 (Week 3):** Add performance database indexes, write proximity search query (Haversine formula for "items near me")

**Phase 4 (Ongoing):** Optimize slow queries, assist Andrea with complex database lookups, manage new migrations as features are added

---

## Andrea's Responsibility Summary

**Phase 1 (Week 1):** Set up URL routing structure, create placeholder views so Briana can start on templates

**Phase 2 (Week 2):** Item CRUD views (create, list, detail, edit, soft-delete), multi-image upload handler

**Phase 3 (Week 3):** Messaging views (send, list conversations, polling endpoint), wishlist toggle endpoint

**Phase 4 (Week 4):** Offer/negotiation views, review submission view

**Phase 5 (Week 5):** Report submission view, block/unblock views, admin dashboard views

**Rule:** Every view must check that the logged-in user has permission before changing any data. A seller cannot edit another seller's listing. A user cannot read another user's messages.

---

## Briana's Responsibility Summary

**Phase 1 (Week 1):** base.html (navbar, footer, Bootstrap CDN links), login page, register page

**Phase 2 (Week 2):** Home page (hero section + category icons + listings grid), item list/browse page with filter sidebar, item detail page (Swiper gallery, Leaflet map, price, seller info)

**Phase 3 (Week 3):** Item create/edit form (multi-image upload with preview), user profile page with tabs, chat/messaging page with JS polling

**Phase 4 (Week 4):** Notification page and navbar badge, report form, block/unblock UI, admin dashboard

**Phase 5 (Week 9-10):** Mobile responsive testing and fixes, 404/500 error pages, final polish

**Rule:** Every POST form needs a CSRF token. Every file upload form needs `enctype="multipart/form-data"`. Every template that uses static files needs `{% load static %}` at the top.

---

## Development Rules for the Whole Team

1. Never push directly to main — always use a feature branch and open a Pull Request
2. Pull the latest changes from main before starting any new work
3. The .env file is never committed to GitHub — it contains passwords and secret keys
4. The CustomUser model (AUTH_USER_MODEL) must be set before the first migration is run — this is Ledio's job on Day 1
5. Items are never hard-deleted from the database — always use soft delete (is_deleted = True)
6. Run the test checklist after completing each phase before moving to the next
7. Ask for help in the team group chat before spending more than 1 hour stuck on a problem

---

## Deployment Checklist (Sprint 5)

- DEBUG is set to False
- SECRET_KEY is a new randomly generated key (not the development one)
- ALLOWED_HOSTS includes the Railway domain
- Database is PostgreSQL on Railway (not SQLite)
- All environment variables are set in Railway dashboard
- collectstatic has been run
- All migrations are applied on the production database
- HTTPS is working (padlock shows in browser)
- Email verification works in production
- A superuser account exists on the production database
- The site loads on mobile without layout issues

---

## Quick Reference: Where Each File Lives

| What | File Path |
|---|---|
| Project settings | config/settings.py |
| Main URL routing | config/urls.py |
| CustomUser model | users/models.py |
| Authentication views | users/views.py |
| All marketplace models | marketplace/models.py |
| All marketplace views | marketplace/views.py |
| Marketplace URL routing | marketplace/urls.py |
| Filter definitions | marketplace/filters.py |
| Category fixture data | marketplace/fixtures/categories.json |
| Base HTML template | templates/base.html |
| Login page | templates/account/login.html |
| Register page | templates/account/signup.html |
| Home/browse page | templates/marketplace/item_list.html |
| Item detail page | templates/marketplace/item_detail.html |
| Create item form | templates/marketplace/item_create.html |
| Chat page | templates/marketplace/inbox.html |
| User profile page | templates/users/profile.html |
| Notifications page | templates/notifications/list.html |
| Admin dashboard | templates/admin_dashboard/dashboard.html |
| Custom CSS | static/css/main.css |
| Shared JS utilities | static/js/utils.js |
| Notification badge poller | static/js/polling.js |
| Secrets file (local only) | .env |
| Package list | requirements.txt |
| Railway start command | Procfile |
