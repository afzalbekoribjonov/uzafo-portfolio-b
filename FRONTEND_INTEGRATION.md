# Frontend integration map

This backend was designed against the latest uploaded frontend snapshot.

## Frontend data groups audited

1. `profile`
2. `resume`
3. `projects`
4. `blog posts`
5. `discussions`
6. `site`
7. media values currently stored as:
   - `project.cover`
   - `post.cover`
   - `content[].src`
   - `video.src`

## Existing `src/lib/api-service.ts` mapping

These functions can be switched almost directly to the live backend:

- `fetchProfile()` -> `GET /api/profile`
- `patchProfile(data)` -> `PATCH /api/profile`
- `fetchProjects()` -> `GET /api/projects`
- `createProject(data)` -> `POST /api/projects`
- `updateProject(slug, data)` -> `PATCH /api/projects/{slug}`
- `deleteProject(slug)` -> `DELETE /api/projects/{slug}`
- `fetchPosts()` -> `GET /api/posts`
- `createPost(data)` -> `POST /api/posts`
- `updatePost(slug, data)` -> `PATCH /api/posts/{slug}`
- `deletePostApi(slug)` -> `DELETE /api/posts/{slug}`
- `addComment(slug, comment)` -> `POST /api/posts/{slug}/comments`
- `deleteComment(slug, commentId)` -> `DELETE /api/posts/{slug}/comments/{commentId}`
- `fetchDiscussions()` -> `GET /api/discussions`
- `createDiscussion(data)` -> `POST /api/discussions`
- `updateDiscussion(slug, data)` -> `PATCH /api/discussions/{slug}`
- `deleteDiscussion(slug)` -> `DELETE /api/discussions/{slug}`
- `addReply(slug, reply)` -> `POST /api/discussions/{slug}/replies`
- `deleteReply(slug, replyId)` -> `DELETE /api/discussions/{slug}/replies/{replyId}`
- `fetchResume()` -> `GET /api/resume`
- `patchResume(data)` -> `PATCH /api/resume`

## Auth integration

Recommended frontend token flow:

1. `POST /api/auth/login`
2. Store `accessToken` and `refreshToken`
3. Add `Authorization: Bearer <accessToken>` for protected requests
4. On 401, call `POST /api/auth/refresh`

## ImageKit upload flow for current editors

Replace current `FileReader -> data URL -> set cover/src` flow with:

1. Call `POST /api/media/upload-auth`
2. Use ImageKit JS SDK `.upload(...)`
3. Call `POST /api/media/complete` with ImageKit response
4. Use returned `media.url` as `cover` or `blocks[].src`

This makes the frontend change small because the UI still receives normal URLs.

## Suggested first frontend patches

1. Add `Authorization` header in `src/lib/api-service.ts`
2. Create a small `uploadMedia(file, ownerType, ownerSlug, role)` helper
3. Update these upload points:
   - `portfolio-detail-client.tsx`
   - `blog-detail-client.tsx`
   - `content-block-editor.tsx`
4. Replace demo auth from `src/lib/auth.ts` with live auth endpoints
