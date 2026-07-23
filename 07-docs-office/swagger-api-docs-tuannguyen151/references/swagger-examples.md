# Swagger Documentation Examples — Comment Feature

Complete reference implementation showing all Swagger decorators for a `Comment` resource.

---

## 1. DTO: `CreateCommentDto`

```typescript
// src/adapters/controllers/comments/dto/create-comment.dto.ts
import { ApiProperty } from '@nestjs/swagger'
import {
  IsDateString,
  IsEnum,
  IsNotEmpty,
  IsNumber,
  IsOptional,
  IsString,
  MaxLength,
} from 'class-validator'
import { CommentVisibilityEnum } from '@domain/entities/comment.entity'

export class CreateCommentDto {
  @ApiProperty({
    required: true,
    maxLength: 10000,
    description: 'Comment body text',
  })
  @IsNotEmpty()
  @IsString()
  @MaxLength(10000)
  body!: string

  @ApiProperty({
    required: true,
    description: 'ID of the task this comment belongs to',
  })
  @IsNotEmpty()
  @IsNumber()
  taskId!: number

  @ApiProperty({
    required: false,
    enum: CommentVisibilityEnum,
    description: 'Visibility of the comment: Public or Private',
  })
  @IsOptional()
  @IsEnum(CommentVisibilityEnum)
  visibility?: CommentVisibilityEnum

  @ApiProperty({
    required: false,
    type: Date,
    description: 'Scheduled publish date for the comment',
  })
  @IsOptional()
  @IsDateString()
  publishAt?: Date
}
```

---

## 2. DTO: `UpdateCommentDto`

```typescript
// src/adapters/controllers/comments/dto/update-comment.dto.ts
import { ApiProperty } from '@nestjs/swagger'
import { IsEnum, IsOptional, IsString, MaxLength } from 'class-validator'
import { CommentVisibilityEnum } from '@domain/entities/comment.entity'

export class UpdateCommentDto {
  @ApiProperty({
    required: false,
    maxLength: 10000,
    description: 'Updated comment body text',
  })
  @IsOptional()
  @IsString()
  @MaxLength(10000)
  body?: string

  @ApiProperty({
    required: false,
    enum: CommentVisibilityEnum,
    description: 'Visibility of the comment: Public or Private',
  })
  @IsOptional()
  @IsEnum(CommentVisibilityEnum)
  visibility?: CommentVisibilityEnum
}
```

---

## 3. DTO: `GetListCommentsDto`

```typescript
// src/adapters/controllers/comments/dto/get-list-comments.dto.ts
import { ApiProperty } from '@nestjs/swagger'
import { IsNumber, IsOptional, IsPositive, Min } from 'class-validator'
import { Type } from 'class-transformer'

export class GetListCommentsDto {
  @ApiProperty({
    required: false,
    description: 'Filter comments by task ID',
  })
  @IsOptional()
  @IsNumber()
  @Type(() => Number)
  taskId?: number

  @ApiProperty({
    required: false,
    description: 'Page number (starts at 1)',
    default: 1,
  })
  @IsOptional()
  @IsPositive()
  @Type(() => Number)
  page?: number

  @ApiProperty({
    required: false,
    description: 'Number of items per page',
    default: 20,
  })
  @IsOptional()
  @IsPositive()
  @Min(1)
  @Type(() => Number)
  limit?: number
}
```

---

## 4. Presenter: `GetDetailCommentPresenter`

```typescript
// src/adapters/controllers/comments/presenters/get-detail-comment.presenter.ts
import { ApiProperty } from '@nestjs/swagger'
import {
  CommentEntity,
  CommentVisibilityEnum,
} from '@domain/entities/comment.entity'

export class GetDetailCommentPresenter {
  @ApiProperty()
  id: number

  @ApiProperty()
  body: string

  @ApiProperty()
  taskId: number

  @ApiProperty({
    enum: CommentVisibilityEnum,
    description: 'Visibility of the comment: Public or Private',
  })
  visibility: CommentVisibilityEnum

  @ApiProperty({ required: false })
  publishAt?: Date

  @ApiProperty()
  createdAt: Date

  @ApiProperty()
  updatedAt: Date

  constructor(comment: CommentEntity) {
    this.id = Number(comment.id)
    this.body = comment.body
    this.taskId = Number(comment.taskId)
    this.visibility = comment.visibility
    this.publishAt = comment.publishAt
    this.createdAt = comment.createdAt
    this.updatedAt = comment.updatedAt
  }
}
```

---

## 5. Presenter: `CreateCommentPresenter`

```typescript
// src/adapters/controllers/comments/presenters/create-comment.presenter.ts
import { GetDetailCommentPresenter } from './get-detail-comment.presenter'

// Inherits all @ApiProperty decorators from GetDetailCommentPresenter
export class CreateCommentPresenter extends GetDetailCommentPresenter {}
```

---

## 6. Presenter: `GetListCommentsPresenter`

```typescript
// src/adapters/controllers/comments/presenters/get-list-comments.presenter.ts
import { type CommentEntity } from '@domain/entities/comment.entity'
import { GetDetailCommentPresenter } from './get-detail-comment.presenter'

export class GetListCommentsPresenter extends GetDetailCommentPresenter {
  static fromList(comments: CommentEntity[]): GetDetailCommentPresenter[] {
    return comments.map((comment) => new GetDetailCommentPresenter(comment))
  }
}
```

---

## 7. Controller: `CommentsController` (fully documented)

```typescript
// src/adapters/controllers/comments/comments.controller.ts
import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseIntPipe,
  Patch,
  Post,
  Query,
  UseGuards,
} from '@nestjs/common'
import {
  ApiBearerAuth,
  ApiExtraModels,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger'

import { CreateCommentUseCase } from '@use-cases/comments/create-comment.use-case'
import { DeleteCommentUseCase } from '@use-cases/comments/delete-comment.use-case'
import { GetDetailCommentUseCase } from '@use-cases/comments/get-detail-comment.use-case'
import { GetListCommentsUseCase } from '@use-cases/comments/get-list-comments.use-case'
import { UpdateCommentUseCase } from '@use-cases/comments/update-comment.use-case'

import { CheckPolicies } from '../common/decorators/check-policies.decorator'
import {
  ApiCreatedResponseType,
  ApiResponseType,
} from '../common/decorators/swagger-response.decorator'
import { User } from '../common/decorators/user.decorator'
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard'
import { PoliciesGuard } from '../common/guards/policies.guard'

import { CreateCommentDto } from './dto/create-comment.dto'
import { GetListCommentsDto } from './dto/get-list-comments.dto'
import { UpdateCommentDto } from './dto/update-comment.dto'

import { CreateCommentPresenter } from './presenters/create-comment.presenter'
import { GetDetailCommentPresenter } from './presenters/get-detail-comment.presenter'
import { GetListCommentsPresenter } from './presenters/get-list-comments.presenter'

@Controller('comments')
@ApiTags('Comments')
@ApiBearerAuth()
@ApiResponse({ status: 401, description: 'No authorization token was found' })
@ApiResponse({ status: 500, description: 'Internal error' })
@ApiResponse({ status: 403, description: 'Forbidden access' })
@UseGuards(JwtAuthGuard, PoliciesGuard)
export class CommentsController {
  constructor(
    private readonly getListCommentsUseCase: GetListCommentsUseCase,
    private readonly createCommentUseCase: CreateCommentUseCase,
    private readonly getDetailCommentUseCase: GetDetailCommentUseCase,
    private readonly updateCommentUseCase: UpdateCommentUseCase,
    private readonly deleteCommentUseCase: DeleteCommentUseCase,
  ) {}

  // ── LIST ────────────────────────────────────────────────────────────────────

  @Get()
  @ApiOperation({ summary: 'List', description: 'List comments' })
  @ApiExtraModels(GetListCommentsPresenter)
  @ApiResponseType(GetListCommentsPresenter, true)      // true = returns array
  @CheckPolicies({ action: 'read', subject: 'Comment' })
  async findAll(
    @Query() dto: GetListCommentsDto,
    @User('id') userId: number,
  ) {
    const comments = await this.getListCommentsUseCase.execute({
      ...dto,
      userId,
    })
    return GetListCommentsPresenter.fromList(comments)
  }

  // ── CREATE ──────────────────────────────────────────────────────────────────

  @Post()
  @ApiOperation({ summary: 'Create', description: 'Create a comment' })
  @ApiExtraModels(CreateCommentPresenter)
  @ApiCreatedResponseType(CreateCommentPresenter, false) // false = single object
  @ApiResponse({ status: 400, description: 'Bad request' })
  @CheckPolicies({ action: 'create', subject: 'Comment' })
  async create(
    @Body() dto: CreateCommentDto,
    @User('id') userId: number,
  ) {
    const comment = await this.createCommentUseCase.execute(
      {
        body: dto.body,
        taskId: dto.taskId,
        visibility: dto.visibility,
        publishAt: dto.publishAt,
      },
      userId,
    )
    return new CreateCommentPresenter(comment)
  }

  // ── DETAIL ──────────────────────────────────────────────────────────────────

  @Get(':id')
  @ApiOperation({ summary: 'Detail', description: 'Get comment by id' })
  @ApiNotFoundResponse({ description: 'Comment not found' })
  @ApiExtraModels(GetDetailCommentPresenter)
  @ApiResponseType(GetDetailCommentPresenter, false)    // false = single object
  @CheckPolicies({ action: 'read', subject: 'Comment' })
  async findOne(
    @User('id') userId: number,
    @Param('id', ParseIntPipe) id: number,
  ) {
    const comment = await this.getDetailCommentUseCase.execute({ id, userId })
    return new GetDetailCommentPresenter(comment)
  }

  // ── UPDATE ──────────────────────────────────────────────────────────────────

  @Patch(':id')
  @ApiOperation({ summary: 'Update', description: 'Update a comment' })
  @ApiNotFoundResponse({ description: 'Comment not found' })
  @ApiOkResponse({ description: 'Comment updated' })   // plain boolean — no presenter
  @CheckPolicies({ action: 'update', subject: 'Comment' })
  async update(
    @User('id') userId: number,
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: UpdateCommentDto,
  ) {
    return this.updateCommentUseCase.execute(
      { id, userId },
      { body: dto.body, visibility: dto.visibility },
    )
  }

  // ── DELETE ──────────────────────────────────────────────────────────────────

  @Delete(':id')
  @ApiOperation({ summary: 'Delete', description: 'Delete a comment' })
  @ApiNotFoundResponse({ description: 'Comment not found' })
  @ApiOkResponse({ description: 'Comment deleted' })   // plain boolean — no presenter
  @CheckPolicies({ action: 'delete', subject: 'Comment' })
  async remove(
    @User('id') userId: number,
    @Param('id', ParseIntPipe) id: number,
  ) {
    return this.deleteCommentUseCase.execute({ id, userId })
  }
}
```

---

## Key patterns at a glance

| Situation | Decorator to use |
|---|---|
| GET returning a list | `@ApiResponseType(Presenter, true)` |
| GET returning a single item | `@ApiResponseType(Presenter, false)` |
| POST creating a resource | `@ApiCreatedResponseType(Presenter, false)` |
| PATCH/DELETE with no presenter | `@ApiOkResponse({ description: '...' })` |
| Endpoint can return 404 | `@ApiNotFoundResponse({ description: '...' })` |
| Any endpoint using a custom presenter | `@ApiExtraModels(Presenter)` — always required |
| Enum field in DTO | `@ApiProperty({ enum: EnumName, description: '...' })` |
| Date field in DTO | `@ApiProperty({ type: Date })` |
| Optional DTO field | `@ApiProperty({ required: false, ... })` |
| Required DTO field | `@ApiProperty({ required: true, ... })` |
