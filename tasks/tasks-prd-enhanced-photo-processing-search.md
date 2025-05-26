# Task List: Enhanced Photo Processing and Search Feature

Based on PRD: `prd-enhanced-photo-processing-search.md`

## Relevant Files

- `backend/photo_service.py` - Contains photo processing functions that need updates for automatic embedding generation and 512x512 resizing
- `backend/routes.py` - Contains upload and search endpoints that need integration with new processing pipeline
- `backend/models.py` - Photo model that may need updates for better integration with vector processing
- `backend/constants.py` - Configuration constants for Pinecone and vector processing

### Notes

- Focus on backend changes only as specified in PRD non-goals (no frontend changes)
- Ensure backward compatibility with existing functionality
- Use existing Pinecone and Vertex AI configurations

## Tasks

- [ ] 1.0 Update Photo Upload Processing to Include Automatic Vector Embedding Generation
  - [x] 1.1 Modify `upload_photos_batch()` function in `routes.py` to call vector processing after PostgreSQL insertion
  - [x] 1.2 Update photo creation flow to ensure PostgreSQL photo ID is available before vector processing
  - [x] 1.3 Integrate embedding generation call for each successfully uploaded photo
  - [x] 1.4 Add vector storage to Pinecone using PostgreSQL photo ID as vector identifier

- [ ] 2.0 Create Enhanced Photo Resizing Function for 512x512 Square Format  
  - [ ] 2.1 Create new function `resize_to_square()` in `photo_service.py` for 512x512 resizing
  - [ ] 2.2 Implement center cropping logic for non-square images
  - [ ] 2.3 Update `get_resized_image_bytes()` function to use 512x512 instead of proportional resizing
  - [ ] 2.4 Test resizing function with various image aspect ratios

- [ ] 3.0 Modify Pinecone Integration to Use PostgreSQL Photo IDs as Vector Identifiers
  - [ ] 3.1 Update `update_index()` function to accept photo ID instead of file path as vector ID
  - [ ] 3.2 Modify vector metadata structure to include PostgreSQL photo ID
  - [ ] 3.3 Update `exists_in_index()` function to check by photo ID instead of file path
  - [ ] 3.4 Create new function `gen_image_embedding_from_base64()` to process base64 data instead of file paths

- [ ] 4.0 Update Search Endpoint to Return Complete Photo Objects from PostgreSQL
  - [ ] 4.1 Modify `search_photos()` function to extract photo IDs from Pinecone results
  - [ ] 4.2 Add PostgreSQL query to fetch Photo objects by IDs from vector search results
  - [ ] 4.3 Update `search_photos_endpoint()` in `routes.py` to return full Photo objects
  - [ ] 4.4 Handle case where photo exists in Pinecone but not in PostgreSQL with appropriate logging

- [ ] 5.0 Implement Comprehensive Error Handling and Logging for Photo Processing Pipeline
  - [ ] 5.1 Add structured logging throughout photo processing functions
  - [ ] 5.2 Implement error handling in upload flow to skip failed photos without breaking batch
  - [ ] 5.3 Add logging for Pinecone-PostgreSQL data inconsistencies
  - [ ] 5.4 Update response format to include processing statistics (success count, error count, error details) 