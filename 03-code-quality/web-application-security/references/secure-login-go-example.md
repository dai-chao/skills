# Secure Login Handler Example (Go)

A hardened Go login handler using parameterization, bcrypt, rate limiting, and secure cookies.

## Full example

```go
package main

import (
    "database/sql"
    "encoding/json"
    "errors"
    "log"
    "net/http"
    "time"

    "golang.org/x/crypto/bcrypt"
    _ "github.com/go-sql-driver/mysql"
)

type LoginReq struct {
    UserName string `json:"userName"` // matches the frontend
    Password string `json:"password"`
}

type UserService struct {
    db *sql.DB
}

func (s *UserService) Login(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }

    var req LoginReq
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        // Generic error; do not echo the body or parsing details
        http.Error(w, "invalid request", http.StatusBadRequest)
        return
    }

    // Basic validation
    if req.UserName == "" || req.Password == "" || len(req.UserName) > 64 || len(req.Password) > 128 {
        http.Error(w, "invalid credentials", http.StatusBadRequest)
        return
    }

    // Look up user with parameterization (defense against SQL injection)
    var hashed string
    err := s.db.QueryRow(
        "SELECT password FROM sys_user WHERE userName = ? AND status = 1",
        req.UserName,
    ).Scan(&hashed)

    if err == sql.ErrNoRows {
        http.Error(w, "invalid credentials", http.StatusUnauthorized)
        return
    }
    if err != nil {
        log.Printf("login db error: %v", err)
        http.Error(w, "invalid credentials", http.StatusInternalServerError)
        return
    }

    // Constant-time password comparison
    if err := bcrypt.CompareHashAndPassword([]byte(hashed), []byte(req.Password)); err != nil {
        http.Error(w, "invalid credentials", http.StatusUnauthorized)
        return
    }

    // Issue token and set secure cookie
    token := generateJWT(req.UserName) // implement with short expiry
    http.SetCookie(w, &http.Cookie{
        Name:     "token",
        Value:    token,
        Path:     "/",
        HttpOnly: true,
        Secure:   true,
        SameSite: http.SameSiteStrictMode,
        MaxAge:   3600,
    })

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]any{
        "code": 0,
        "data": map[string]string{"token": token},
    })
}

func generateJWT(userName string) string {
    // Use a proper JWT library with short expiry and strong signing key
    return "signed-token"
}
```

## Security headers middleware

```go
func SecurityHeaders(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("X-Content-Type-Options", "nosniff")
        w.Header().Set("X-Frame-Options", "DENY")
        w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
        w.Header().Set("Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'")
        next.ServeHTTP(w, r)
    })
}
```

## Rate limiting (in-memory example)

```go
import "golang.org/x/time/rate"

var limiters = make(map[string]*rate.Limiter)

func loginLimit(ip string) bool {
    lim, ok := limiters[ip]
    if !ok {
        lim = rate.NewLimiter(rate.Limit(1/60.0), 5)
        limiters[ip] = lim
    }
    return lim.Allow()
}
```

For production, use Redis with a TTL per IP and per username.

## Nginx hardening

```nginx
server {
    listen 443 ssl;
    server_name adminapi.zenya.art;

    server_tokens off;

    location /api/ {
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        proxy_pass http://backend;
    }

    if ($request_method = TRACE) {
        return 444;
    }
}
```
