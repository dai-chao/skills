---
name: swagger-api-docs
description: >
  Activate when the user asks to add swagger docs, document API, add @ApiProperty,
  add swagger response type, add OpenAPI decorators, use ApiResponseType or
  ApiCreatedResponseType, or document an endpoint in the NestJS Clean Architecture project.
  Apply this skill whenever OpenAPI/Swagger documentation must be added or updated
  for controllers, DTOs, or presenters.
---

# Swagger API Documentation Skill

## Overview

This project uses a **custom response wrapper** pattern for all Swagger responses. Every API response is wrapped in `ResponseFormat<T>`, which adds `isArray`, `path`, `duration`, and `method` metadata fields around the actual `data` payload. Two project-specific decorators — `ApiResponseType` and `ApiCreatedResponseType` — replace the standard `@ApiOkResponse` and `@ApiCreatedResponse` decorators to enforce this wrapper in the OpenAPI schema.

Always use the project's custom decorators. Never use raw `@ApiOkResponse` or `@ApiCreatedResponse` for endpoint-level response documentation on resource endpoints.

---

## 1. Import the Custom Decorators

Import from the shared decorators file:

```typescript
import {
  ApiCreatedResponseType,
  ApiResponseType,
} from '../common/decorators/swagger-response.decorator'
```

---

## 2. Controller-Level Decorators

Apply these decorators to every resource controller class — no exceptions:

```typescript
@Controller('comments')
@ApiTags('Comments')                        // Groups all endpoints under "Comments" in Swagger UI
@ApiBearerAuth()                            // Shows the lock icon; marks all endpoints as JWT-protected
@ApiResponse({ status: 401, description: 'No authorization token was found' })
@ApiResponse({ status: 500, description: 'Internal error' })
@ApiResponse({ status: 403, description: 'Forbidden access' })
@UseGuards(JwtAuthGuard, PoliciesGuard)
export class CommentsController { ... }
```

Place `@ApiTags`, `@ApiBearerAuth`, and the three `@ApiResponse` decorators on the class itself so they apply to every endpoint inside it. Do **not** repeat them on individual methods.

---

## 3. Endpoint-Level Decorator Order

Follow this exact decorator ordering on every endpoint method:

```
@Get() / @Post() / @Patch() / @Delete()
@ApiOperation(...)
@ApiExtraModels(PresenterClass)
@ApiResponseType(PresenterClass, isArray)   ← GET/PATCH/DELETE that return data
@ApiCreatedResponseType(PresenterClass, isArray)  ← POST only
@CheckPolicies(...)
```

### GET — list (array)

```typescript
@Get()
@ApiOperation({ summary: 'List', description: 'List comments' })
@ApiExtraModels(GetListCommentsPresenter)
@ApiResponseType(GetListCommentsPresenter, true)   // true = array
@CheckPolicies({ action: 'read', subject: 'Comment' })
async findAll(...) { ... }
```

### GET — single resource

```typescript
@Get(':id')
@ApiOperation({ summary: 'Detail', description: 'Get comment by id' })
@ApiNotFoundResponse({ description: 'Comment not found' })
@ApiExtraModels(GetDetailCommentPresenter)
@ApiResponseType(GetDetailCommentPresenter, false)  // false = single object
@CheckPolicies({ action: 'read', subject: 'Comment' })
async findOne(...) { ... }
```

### POST — create

```typescript
@Post()
@ApiOperation({ summary: 'Create', description: 'Create a comment' })
@ApiExtraModels(CreateCommentPresenter)
@ApiCreatedResponseType(CreateCommentPresenter, false)
@ApiResponse({ status: 400, description: 'Bad request' })
@CheckPolicies({ action: 'create', subject: 'Comment' })
async create(...) { ... }
```

### PATCH — update (no presenter, plain response)

```typescript
@Patch(':id')
@ApiOperation({ summary: 'Update', description: 'Update a comment' })
@ApiNotFoundResponse({ description: 'Comment not found' })
@ApiOkResponse({ description: 'Comment updated' })
@CheckPolicies({ action: 'update', subject: 'Comment' })
async update(...) { ... }
```

---

## 4. `@ApiExtraModels` Is Mandatory

`@ApiExtraModels(PresenterClass)` must appear on **every** endpoint that uses `@ApiResponseType` or `@ApiCreatedResponseType`. Without it, Swagger cannot resolve the `$ref` to the presenter class and the schema will be broken. Always pair them:

```typescript
@ApiExtraModels(CreateCommentPresenter)
@ApiCreatedResponseType(CreateCommentPresenter, false)
```

---

## 5. DTOs — `@ApiProperty` Rules

Add `@ApiProperty` to **every** field in every DTO. Never leave a field undocumented.

```typescript
export class CreateCommentDto {
  @ApiProperty({ required: true, maxLength: 10000, description: 'Comment body' })
  @IsNotEmpty()
  @IsString()
  @MaxLength(10000)
  body!: string

  @ApiProperty({ required: false, enum: CommentVisibilityEnum, description: 'Visibility: Public or Private' })
  @IsOptional()
  @IsEnum(CommentVisibilityEnum)
  visibility?: CommentVisibilityEnum

  @ApiProperty({ required: false, type: Date, description: 'Scheduled publish date' })
  @IsOptional()
  @IsDateString()
  publishAt?: Date

  @ApiProperty({ required: true, description: 'Parent task ID' })
  @IsNotEmpty()
  @IsNumber()
  taskId!: number
}
```

**DTO `@ApiProperty` field reference:**

| Scenario | Options to include |
|---|---|
| Required string with length limit | `required: true, maxLength: N, description: '...'` |
| Optional string | `required: false, maxLength: N, description: '...'` |
| Enum field | `required: true/false, enum: EnumName, description: '...'` |
| Date field | `required: false, type: Date, description: '...'` |
| Number field | `required: true, description: '...'` |
| Boolean field | `required: false, description: '...'` |

---

## 6. Presenters — `@ApiProperty` Rules

Add `@ApiProperty()` to every field. Use `{ enum: EnumName }` for enum fields. Use `{ required: false }` for optional fields. Include a `description` on enum fields to document the enum values.

```typescript
export class GetDetailCommentPresenter {
  @ApiProperty()
  id: number

  @ApiProperty()
  body: string

  @ApiProperty({ enum: CommentVisibilityEnum, description: 'Public or Private' })
  visibility: CommentVisibilityEnum

  @ApiProperty({ required: false })
  publishAt?: Date

  constructor(comment: CommentEntity) {
    this.id = comment.id
    this.body = comment.body
    this.visibility = comment.visibility
    this.publishAt = comment.publishAt
  }
}
```

Presenters that extend another presenter inherit its `@ApiProperty` decorators — no need to re-declare them:

```typescript
export class CreateCommentPresenter extends GetDetailCommentPresenter {}
```

---

## 7. How `ApiResponseType` and `ApiCreatedResponseType` Work

Both decorators wrap the presenter inside `ResponseFormat<T>` using `allOf` composition in the OpenAPI schema. The resulting schema tells Swagger that the response body is:

```json
{
  "isArray": true,
  "path": "/comments",
  "duration": "12ms",
  "method": "GET",
  "data": [ /* array of CommentPresenter */ ]
}
```

Pass `true` as the second argument when the endpoint returns a list. Pass `false` when it returns a single object. This controls whether `data` is typed as `array` or `object` in the schema.

---

## 8. Additional Response Decorators

Use these for non-standard cases:

- `@ApiNotFoundResponse({ description: '...' })` — add on any endpoint that can throw 404
- `@ApiResponse({ status: 400, description: 'Bad request' })` — add on POST/PATCH when input validation can fail
- `@ApiOkResponse({ description: '...' })` — use **only** for PATCH/DELETE that return a plain boolean or message (not a presenter)

---

## 9. Checklist Before Committing

- [ ] Controller class has `@ApiTags`, `@ApiBearerAuth`, and all three `@ApiResponse` status decorators
- [ ] Every GET endpoint uses `@ApiResponseType` (not `@ApiOkResponse`)
- [ ] Every POST endpoint uses `@ApiCreatedResponseType` (not `@ApiCreatedResponse`)
- [ ] Every `@ApiResponseType` / `@ApiCreatedResponseType` is paired with `@ApiExtraModels`
- [ ] Every DTO field has `@ApiProperty` with appropriate options
- [ ] Every presenter field has `@ApiProperty` (with `{ enum }` where applicable)
- [ ] `isArray` flag matches the actual return type (array vs single)
- [ ] `@ApiNotFoundResponse` is present on endpoints that can return 404

---

## 10. File Placement

| File type | Location |
|---|---|
| Swagger response decorators | `src/adapters/controllers/common/decorators/swagger-response.decorator.ts` |
| DTO | `src/adapters/controllers/[feature]/dto/[action]-[feature].dto.ts` |
| Presenter | `src/adapters/controllers/[feature]/presenters/[action]-[feature].presenter.ts` |
| Controller | `src/adapters/controllers/[feature]/[feature].controller.ts` |
