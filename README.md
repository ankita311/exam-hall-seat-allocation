# Seat Allocation System

A FastAPI-based system for managing class student data and performing round-robin seat allocation for examinations. The system allows you to upload student data from Excel files, configure examination rooms, and automatically allocate seats ensuring students from different classes with different courses are paired together.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Seat Allocation Output Grid](#seat-allocation-output-grid)
- [Usage Examples](#usage-examples)

## Requirements

- Python 3.12 or higher
- PostgreSQL database (optional, for future database integration)
- Dependencies listed in `pyproject.toml`:
  - FastAPI
  - Uvicorn
  - Pandas
  - OpenPyXL
  - SQLAlchemy
  - Alembic
  - psycopg2

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd seat-allocation
```

2. Create a virtual environment (recommended):
```bash
python -m venv .venv
```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```
Or if using `uv`:
```bash
uv pip install -e .
```

## Configuration

### Database Configuration (Optional)

The application uses SQLAlchemy for database operations. To configure the database connection, edit `api/database.py` and update the `SQLALCHEMY_DATABASE_URL` variable with your database connection string.

For Alembic migrations, the database URL is automatically synchronized from `api/database.py` to `alembic.ini`.

### Data Directories

The application creates the following directories automatically:
- `data/classes/` - Stores class student data in JSON format
- `data/rooms/` - Stores room configuration data in JSON format

These directories are created automatically when the application starts.

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn api.main:app --reload
```

2. The API will be available at:
```
http://localhost:8000
```

3. Access the interactive API documentation at:
```
http://localhost:8000/docs
```

## API Endpoints

### Class Management

#### POST /add-class
Upload an Excel file containing student data for a class.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Parameters:
  - `class_name` (string, form field): Name of the class
  - `file` (file, form field): Excel file (.xlsx or .xls) containing student data

**Excel File Format:**
The Excel file must contain the following columns:
- `roll_no`: Student roll number
- `course`: Course/subject name

**Response:**
Returns a JSON object with:
- `message`: Success message
- `class_name`: Name of the class
- `total_students`: Number of students in the class
- `file_saved`: Path to the saved JSON file
- `data`: Complete class data structure

#### GET /classes
List all stored classes with their metadata.

**Response:**
Returns a JSON object with:
- `total_classes`: Total number of classes
- `classes`: Array of class objects containing:
  - `class_name`: Name of the class
  - `uploaded_at`: Upload timestamp
  - `total_students`: Number of students
  - `file`: JSON filename

#### GET /classes/{class_name}
Retrieve detailed data for a specific class.

**Response:**
Returns a JSON object with:
- `class_name`: Name of the class
- `uploaded_at`: Upload timestamp
- `total_students`: Number of students
- `students`: Array of student objects with `roll_no` and `course`

### Room Management

#### POST /add-room
Create a new examination room configuration.

**Request:**
- Method: POST
- Content-Type: application/json
- Body:
```json
{
  "room_name": "E-001",
  "rows": 4,
  "cols": 8
}
```

**Parameters:**
- `room_name` (string): Name/identifier of the room
- `rows` (integer): Number of rows in the room
- `cols` (integer): Number of columns (benches) in each row

**Note:** Each bench has a capacity of 2 students.

**Response:**
Returns a JSON object with:
- `message`: Success message
- `room_name`: Name of the room
- `total_capacity`: Total seating capacity (rows × cols × 2)
- `file_saved`: Path to the saved JSON file
- `data`: Complete room data structure

#### GET /rooms
List all stored rooms with their metadata.

**Response:**
Returns a JSON object with:
- `total_rooms`: Total number of rooms
- `rooms`: Array of room objects containing:
  - `room_name`: Name of the room
  - `created_at`: Creation timestamp
  - `total_capacity`: Room capacity
  - `file`: JSON filename

#### GET /rooms/{room_name}
Retrieve detailed data for a specific room.

**Response:**
Returns a JSON object with:
- `room_name`: Name of the room
- `created_at`: Creation timestamp
- `configuration`: Room configuration details
- `layout`: Layout information

### Seat Allocation

#### POST /allocation/allocate-seats
Perform round-robin seat allocation for two classes in a room.

**Request:**
- Method: POST
- Content-Type: application/json
- Body:
```json
{
  "class1_name": "cse-a",
  "class2_name": "cse-b",
  "room_name": "E-001",
  "date": "15th Dec 2024"
}
```

**Parameters:**
- `class1_name` (string, required): Name of the first class
- `class2_name` (string, required): Name of the second class
- `room_name` (string, required): Name of the room for allocation
- `date` (string, optional): Examination date (defaults to current date if not provided)

**Response:**
Returns a JSON object with the complete seating allocation data. See [Seat Allocation Output Grid](#seat-allocation-output-grid) section for detailed structure.

**Allocation Rules:**
1. Each student is allocated exactly once (no duplicates)
2. Two students from different classes are paired on each bench
3. Students with the same course/subject are not paired together (when possible)
4. If one class has more students than the other, remaining students sit alone
5. Empty benches are left empty if no students remain

## Seat Allocation Output Grid

The seat allocation endpoint returns a structured JSON response with a 2D grid representing the room layout. The grid structure is organized as follows:

### Response Structure

```json
{
  "hall": "E-001",
  "date": "15th Dec 2024",
  "grid": [
    [
      ["CS101", "ME201"],
      ["CS102", "ME202"],
      ["CS103", "ME203"],
      ["CS104", "ME204"]
    ],
    [
      ["CS105", "ME205"],
      ["ME206"],
      [],
      []
    ]
  ],
  "class1": "cse-a",
  "class2": "cse-b",
  "total_students_class1": 5,
  "total_students_class2": 6,
  "room_configuration": {
    "rows": 4,
    "cols": 8,
    "total_capacity": 64
  }
}
```

### Grid Structure Explanation

The `grid` field is a three-dimensional array organized as:

1. **Outer Array (Rows):** Represents each row in the examination room
   - Index 0 = Front row
   - Index n-1 = Back row

2. **Middle Array (Columns/Benches):** Represents each bench in that row
   - Index 0 = Leftmost bench
   - Index n-1 = Rightmost bench

3. **Inner Array (Seats):** Represents the two seats on each bench
   - Contains 0 to 2 student roll numbers
   - `["ROLL1", "ROLL2"]` = Both seats occupied
   - `["ROLL1"]` = Only first seat occupied (student sitting alone)
   - `[]` = Bench is empty

### Grid Interpretation Example

For a room with 4 rows and 8 columns:

```
Row 0 (Front):  [Bench0, Bench1, Bench2, ..., Bench7]
Row 1:          [Bench0, Bench1, Bench2, ..., Bench7]
Row 2:          [Bench0, Bench1, Bench2, ..., Bench7]
Row 3 (Back):   [Bench0, Bench1, Bench2, ..., Bench7]
```

Each bench contains:
- Seat 0 (Left seat)
- Seat 1 (Right seat)

### Accessing Specific Seats

To access a specific seat in the grid:
- `grid[row_index][column_index]` = Array of roll numbers for that bench
- `grid[row_index][column_index][0]` = First student on the bench (left seat)
- `grid[row_index][column_index][1]` = Second student on the bench (right seat), if present

### Visual Representation

A typical grid output can be visualized as:

```
Row 0:  [CS101, ME201]  [CS102, ME202]  [CS103, ME203]  [CS104, ME204]  ...
Row 1:  [CS105, ME205]  [ME206]         []              []              ...
Row 2:  []              []              []              []              ...
Row 3:  []              []              []              []              ...
```

Where:
- Pairs like `[CS101, ME201]` indicate two students sitting together
- Single entries like `[ME206]` indicate a student sitting alone
- Empty arrays `[]` indicate an empty bench

## Usage Examples

### Example 1: Adding a Class

Using cURL:
```bash
curl -X POST "http://localhost:8000/add-class" \
  -F "class_name=cse-a" \
  -F "file=@students.xlsx"
```

Using Python requests:
```python
import requests

url = "http://localhost:8000/add-class"
files = {"file": open("students.xlsx", "rb")}
data = {"class_name": "cse-a"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Example 2: Adding a Room

Using cURL:
```bash
curl -X POST "http://localhost:8000/add-room" \
  -H "Content-Type: application/json" \
  -d '{"room_name": "E-001", "rows": 4, "cols": 8}'
```

Using Python requests:
```python
import requests

url = "http://localhost:8000/add-room"
data = {
    "room_name": "E-001",
    "rows": 4,
    "cols": 8
}

response = requests.post(url, json=data)
print(response.json())
```

### Example 3: Allocating Seats

Using cURL:
```bash
curl -X POST "http://localhost:8000/allocation/allocate-seats" \
  -H "Content-Type: application/json" \
  -d '{
    "class1_name": "cse-a",
    "class2_name": "cse-b",
    "room_name": "E-001",
    "date": "15th Dec 2024"
  }'
```

Using Python requests:
```python
import requests

url = "http://localhost:8000/allocation/allocate-seats"
data = {
    "class1_name": "cse-a",
    "class2_name": "cse-b",
    "room_name": "E-001",
    "date": "15th Dec 2024"
}

response = requests.post(url, json=data)
allocation = response.json()

# Access the grid
grid = allocation["grid"]

# Print seat allocation for row 0, column 0
print(f"Bench at Row 0, Column 0: {grid[0][0]}")

# Iterate through all seats
for row_idx, row in enumerate(grid):
    for col_idx, bench in enumerate(row):
        if bench:
            print(f"Row {row_idx}, Column {col_idx}: {bench}")
```

### Example 4: Retrieving Class Data

```bash
curl "http://localhost:8000/classes/cse-a"
```

### Example 5: Listing All Rooms

```bash
curl "http://localhost:8000/rooms"
```

## Error Handling

The API returns standard HTTP status codes:
- `200 OK`: Request successful
- `400 Bad Request`: Invalid input or validation error
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a `detail` field with error information:
```json
{
  "detail": "Class 'cse-a' not found"
}
```

## Notes

- Student data is stored in JSON format in the `data/classes/` directory
- Room configurations are stored in JSON format in the `data/rooms/` directory
- Each class upload creates a timestamped JSON file
- The seat allocation algorithm ensures no student is allocated twice
- Students with the same course are not paired together when possible
- The system handles cases where class sizes are unequal

## License

[Add your license information here]

