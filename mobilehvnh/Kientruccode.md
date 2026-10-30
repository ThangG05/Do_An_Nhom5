# Flutter Architecture Blueprint

> Bộ khung kiến trúc dùng làm nền tảng lâu dài cho các dự án Flutter.

## 1. Architecture

Dự án sử dụng **Feature-based Architecture**.

Toàn bộ source code được chia thành 3 khu vực chính:

``` text
lib/
├── main.dart
├── app/
├── core/
└── features/
```

``` text
main.dart
   │
   ▼
 app/
   │
   ├──────────────► core/
   │
   └──────────────► features/
```

### Vai trò

``` text
main.dart   → Entry point

app/        → Cấu hình và composition của toàn application

core/       → Infrastructure/shared code không thuộc feature cụ thể

features/   → Business features của application
```

------------------------------------------------------------------------

# 2. Standard Folder Structure

``` text
lib/
│
├── main.dart
│
├── app/
│   ├── app.dart
│   ├── router/
│   └── di/
│
├── core/
│   ├── network/
│   ├── storage/
│   ├── config/
│   ├── constants/
│   ├── errors/
│   ├── utils/
│   ├── theme/
│   └── widgets/
│
└── features/
    │
    ├── auth/
    ├── home/
    ├── user/
    ├── post/
    ├── chat/
    └── ...
```

Không tổ chức toàn bộ project theo kiểu:

``` text
lib/
├── pages/
├── models/
├── providers/
├── services/
└── widgets/
```

Thay vào đó, code liên quan đến cùng một nghiệp vụ được đặt gần nhau:

``` text
features/
├── auth/
├── post/
├── chat/
└── user/
```

------------------------------------------------------------------------

# 3. `app/` --- Application Layer

`app/` chịu trách nhiệm ghép các phần của application lại với nhau.

``` text
app/
├── app.dart
├── router/
│   └── app_router.dart
└── di/
    └── app_dependencies.dart
```

`app/` có thể biết về:

``` text
core/
features/
```

Nhưng feature không nên phụ thuộc ngược vào `app/`.

Dependency:

``` text
            app
           /   \
          ▼     ▼
       core   features
```

------------------------------------------------------------------------

# 4. `core/` --- Shared Infrastructure

`core/` chỉ chứa code có tính chất dùng chung hoặc infrastructure.

``` text
core/
├── network/
│   ├── api_client.dart
│   ├── interceptors/
│   └── network_exception.dart
│
├── storage/
│   ├── secure_storage.dart
│   └── local_storage.dart
│
├── config/
├── constants/
├── errors/
├── utils/
├── theme/
└── widgets/
```

Quy tắc:

``` text
core không chứa business logic của một feature cụ thể.
```

Ví dụ:

``` text
ApiClient           → core
SecureStorage       → core
AppTheme            → core
DateFormatter       → core

PostModel           → KHÔNG thuộc core
ChatProvider        → KHÔNG thuộc core
UserRepository      → KHÔNG thuộc core
```

Nếu code chỉ phục vụ một feature:

``` text
features/<feature>/
```

Nếu code thực sự dùng chung:

``` text
core/
```

------------------------------------------------------------------------

# 5. Feature Structure

Mỗi business feature là một module độc lập.

Cấu trúc chuẩn:

``` text
features/
└── feature_name/
    │
    ├── data/
    │   ├── models/
    │   ├── datasources/
    │   └── repositories/
    │
    ├── domain/
    │   ├── entities/
    │   ├── repositories/
    │   └── usecases/
    │
    └── presentation/
        ├── state/
        ├── pages/
        └── widgets/
```

Ví dụ:

``` text
features/
└── post/
    │
    ├── data/
    │   ├── models/
    │   │   └── post_model.dart
    │   │
    │   ├── datasources/
    │   │   └── post_remote_data_source.dart
    │   │
    │   └── repositories/
    │       └── post_repository_impl.dart
    │
    ├── domain/
    │   ├── entities/
    │   │   └── post.dart
    │   │
    │   ├── repositories/
    │   │   └── post_repository.dart
    │   │
    │   └── usecases/
    │       ├── get_posts.dart
    │       └── create_post.dart
    │
    └── presentation/
        ├── state/
        │   └── post_provider.dart
        │
        ├── pages/
        │   └── post_page.dart
        │
        └── widgets/
            └── post_card.dart
```

------------------------------------------------------------------------

# 6. Layers Inside a Feature

Mỗi feature gồm 3 layer:

``` text
┌─────────────────────────────┐
│       PRESENTATION          │
│                             │
│ Page / Widget / State       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│          DOMAIN             │
│                             │
│ Entity / UseCase / Contract │
└──────────────┬──────────────┘
               ▲
               │ implements
┌──────────────┴──────────────┐
│           DATA              │
│                             │
│ Model / DataSource / Repo   │
└─────────────────────────────┘
```

------------------------------------------------------------------------

# 7. Presentation Layer

``` text
presentation/
├── state/
├── pages/
└── widgets/
```

Presentation chứa code liên quan tới UI và state của UI.

``` text
Page
  │
  ▼
State Manager
  │
  ▼
UseCase
```

Có thể sử dụng bất kỳ state management nào:

``` text
Provider
Riverpod
Bloc
Cubit
ChangeNotifier
```

Kiến trúc không phụ thuộc vào một thư viện state management cụ thể.

Presentation được phép phụ thuộc vào:

``` text
domain/
core/
```

Không nên phụ thuộc trực tiếp vào:

``` text
data/datasources/
```

------------------------------------------------------------------------

# 8. Domain Layer

Domain là phần trung tâm của feature.

``` text
domain/
├── entities/
├── repositories/
└── usecases/
```

Domain mô tả:

``` text
Business Entity
Business Rules
Repository Contract
Use Cases
```

Domain không quan tâm:

``` text
REST API
Dio
Firebase
SQLite
Flutter Widget
JSON
```

Ví dụ:

``` text
domain/
├── entities/
│   └── post.dart
├── repositories/
│   └── post_repository.dart
└── usecases/
    └── get_posts.dart
```

Repository trong domain chỉ là abstraction:

``` dart
abstract class PostRepository {
  Future<List<Post>> getPosts();
}
```

Domain không biết dữ liệu đến từ đâu.

------------------------------------------------------------------------

# 9. Data Layer

``` text
data/
├── models/
├── datasources/
└── repositories/
```

Data layer chịu trách nhiệm lấy và chuyển đổi dữ liệu.

``` text
Remote API
Local DB
Firebase
Cache
      │
      ▼
DataSource
      │
      ▼
Model
      │
      ▼
Repository Implementation
```

Repository implementation thực thi contract từ domain:

``` text
domain
└── PostRepository

        ▲
        │ implements

data
└── PostRepositoryImpl
```

Ví dụ:

``` dart
class PostRepositoryImpl implements PostRepository {
  final PostRemoteDataSource remoteDataSource;

  PostRepositoryImpl(this.remoteDataSource);

  @override
  Future<List<Post>> getPosts() {
    return remoteDataSource.getPosts();
  }
}
```

------------------------------------------------------------------------

# 10. Dependency Rule

Đây là quy tắc quan trọng nhất của kiến trúc.

``` text
Presentation
     │
     ▼
   Domain
     ▲
     │
    Data
```

Hay:

``` text
presentation ─────► domain
data ─────────────► domain
```

Domain không phụ thuộc ngược lại:

``` text
domain ─X─► presentation
domain ─X─► data
```

Infrastructure dùng chung:

``` text
data ─────► core
presentation ─────► core
```

Sơ đồ tổng thể:

``` text
                         app/
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
           core/                     features/
                                         │
                          ┌──────────────┼──────────────┐
                          │              │              │
                         auth           post           chat
                          │              │              │
                    ┌─────┴─────┐  ┌────┴─────┐  ┌────┴─────┐
                    │           │  │          │  │          │
               presentation   data ...       ... ...        ...
                    │           │
                    ▼           │
                  domain ◄──────┘
```

------------------------------------------------------------------------

# 11. Data Flow

Runtime flow:

``` text
Page
 │
 ▼
State Manager
 │
 ▼
UseCase
 │
 ▼
Repository Contract
 │
 ▼
Repository Implementation
 │
 ▼
DataSource
 │
 ▼
API / Database / Firebase
```

Response đi ngược lại:

``` text
API
 │
 ▼
DataSource
 │
 ▼
Model
 │
 ▼
Repository
 │
 ▼
Entity
 │
 ▼
UseCase
 │
 ▼
State Manager
 │
 ▼
UI
```

Tổng quát:

``` text
UI
 ↓
Presentation
 ↓
Domain
 ↓
Data
 ↓
External System

External System
 ↓
Data
 ↓
Domain
 ↓
Presentation
 ↓
UI
```

------------------------------------------------------------------------

# 12. Model vs Entity

Không nên coi Model và Entity là cùng một khái niệm trong project lớn.

### Entity

Thuộc:

``` text
domain/entities/
```

Đại diện cho dữ liệu mà business logic sử dụng.

``` dart
class User {
  final String id;
  final String name;
}
```

### Model

Thuộc:

``` text
data/models/
```

Đại diện dữ liệu từ external source.

``` dart
class UserModel {
  final String id;
  final String fullName;

  factory UserModel.fromJson(Map<String, dynamic> json) {
    ...
  }

  User toEntity() {
    return User(
      id: id,
      name: fullName,
    );
  }
}
```

Luồng:

``` text
JSON
 ↓
Model
 ↓
Entity
 ↓
Domain
```

Nếu backend thay đổi JSON, phần lớn thay đổi được giới hạn trong Data
Layer.

------------------------------------------------------------------------

# 13. Repository Pattern

Repository tạo boundary giữa Domain và nguồn dữ liệu.

``` text
                  DOMAIN
                     │
             Repository Contract
                     ▲
                     │ implements
                     │
                   DATA
                     │
          Repository Implementation
                     │
             ┌───────┴───────┐
             ▼               ▼
       RemoteDataSource  LocalDataSource
             │               │
             ▼               ▼
            API           Database
```

Presentation không cần biết dữ liệu đến từ:

``` text
REST API
Firebase
SQLite
Cache
Mock data
```

------------------------------------------------------------------------

# 14. Feature Independence

Mỗi feature nên có boundary rõ ràng.

``` text
features/
├── auth/
├── user/
├── post/
└── chat/
```

Không nên tạo dependency hỗn loạn:

``` text
post → user → chat → post
```

Tránh circular dependency:

``` text
Feature A
   ↓
Feature B
   ↓
Feature A
```

Nếu nhiều feature cần cùng một infrastructure:

``` text
Feature A ─┐
           ├──► core
Feature B ─┘
```

Không đưa business logic đặc thù vào `core` chỉ để tránh dependency giữa
feature.

------------------------------------------------------------------------

# 15. Public Boundary of a Feature

Khi project lớn, nên giới hạn những gì feature khác được import.

Có thể tạo:

``` text
features/post/post.dart
```

Ví dụ:

``` dart
export 'domain/entities/post.dart';
export 'presentation/pages/post_page.dart';
```

Module khác sử dụng:

``` dart
import 'package:app/features/post/post.dart';
```

thay vì import sâu:

``` dart
import 'package:app/features/post/data/datasources/post_remote_data_source.dart';
```

Điều này giúp internal structure của feature có thể thay đổi mà ít ảnh
hưởng module khác.

------------------------------------------------------------------------

# 16. Feature Template

Khi tạo feature mới, copy cấu trúc:

``` text
feature_name/
│
├── data/
│   ├── models/
│   │   └── .gitkeep
│   ├── datasources/
│   │   └── .gitkeep
│   └── repositories/
│       └── .gitkeep
│
├── domain/
│   ├── entities/
│   │   └── .gitkeep
│   ├── repositories/
│   │   └── .gitkeep
│   └── usecases/
│       └── .gitkeep
│
└── presentation/
    ├── state/
    │   └── .gitkeep
    ├── pages/
    │   └── .gitkeep
    └── widgets/
        └── .gitkeep
```

Không bắt buộc tạo file/thư mục chưa dùng.

Một feature nhỏ có thể bắt đầu:

``` text
feature_name/
├── data/
│   ├── feature_api.dart
│   └── feature_model.dart
│
└── presentation/
    ├── feature_provider.dart
    └── feature_page.dart
```

Sau đó tách thêm layer khi độ phức tạp tăng.

------------------------------------------------------------------------

# 17. Import Rules

Có thể dùng các quy tắc này như luật của codebase:

``` text
RULE 1
presentation có thể import domain.

RULE 2
data có thể import domain.

RULE 3
domain không import presentation.

RULE 4
domain không import data.

RULE 5
feature có thể sử dụng core.

RULE 6
core không import business feature.

RULE 7
UI không gọi DataSource trực tiếp.

RULE 8
UI không gọi HTTP client trực tiếp.

RULE 9
feature không truy cập internal implementation
của feature khác nếu có public boundary.

RULE 10
tránh circular dependency giữa các feature.
```

Dependency hợp lệ:

``` text
app
 │
 ├────────► core
 │
 └────────► features
               │
        ┌──────┴──────┐
        ▼             ▼
 presentation        data
        │             │
        └──────► domain ◄──────┘
                      │
                pure business
```

------------------------------------------------------------------------

# 18. Final Architecture

``` text
lib/
│
├── main.dart
│
├── app/
│   ├── app.dart
│   ├── router/
│   └── di/
│
├── core/
│   ├── network/
│   ├── storage/
│   ├── config/
│   ├── constants/
│   ├── errors/
│   ├── utils/
│   ├── theme/
│   └── widgets/
│
└── features/
    │
    └── <feature>/
        │
        ├── data/
        │   ├── models/
        │   ├── datasources/
        │   └── repositories/
        │
        ├── domain/
        │   ├── entities/
        │   ├── repositories/
        │   └── usecases/
        │
        └── presentation/
            ├── state/
            ├── pages/
            └── widgets/
```

Kiến trúc tổng quát:

``` text
                    ┌─────────────┐
                    │     APP     │
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
             CORE                 FEATURES
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                        AUTH        POST         CHAT
                          │
                   ┌──────┼──────┐
                   ▼      ▼      ▼
                 PRES   DOMAIN  DATA
                   │      ▲      │
                   └─────►│◄─────┘
```

**Dependency direction:**

``` text
Presentation ──► Domain
Data ──────────► Domain

Presentation ──► Core
Data ──────────► Core

App ───────────► Features
App ───────────► Core
```

Domain giữ vị trí trung tâm và không phụ thuộc vào UI, networking,
database hoặc framework-specific implementation.
