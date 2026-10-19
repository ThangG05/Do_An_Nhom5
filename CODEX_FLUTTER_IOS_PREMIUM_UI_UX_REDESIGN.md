# CODEX MASTER PROMPT — FLUTTER iOS-INSPIRED PREMIUM UI/UX REDESIGN

> **Vai trò của bạn (Codex):** Senior Flutter Engineer + iOS UI/UX Designer + Motion/Interaction Designer + Mobile Performance Engineer.
>
> **Nhiệm vụ:** Phân tích toàn bộ dự án Flutter đang mở, sau đó **trực tiếp chỉnh sửa code** để tái thiết kế UI/UX theo phong cách **iOS-inspired, hiện đại, sáng rõ, mềm mại, tươi trẻ, giàu chiều sâu, chuyển động tinh tế và có hiệu ứng 3D có chủ đích**. Không dừng ở việc viết tài liệu hoặc tạo mockup.
>
> **Lưu ý phạm vi:** Đây là yêu cầu về **giao diện và trải nghiệm**, **không phải chuyển Flutter sang Swift/iOS native**. Ứng dụng vẫn build và vận hành trên Flutter cho cả Android lẫn iOS, nhưng ngôn ngữ thiết kế ưu tiên iOS. **Không bắt buộc mọi widget phải là Cupertino**; chọn cách triển khai tối ưu về cảm giác, tính nhất quán và hiệu năng.

---

## 0. CÁCH THỰC HIỆN — BẮT BUỘC

1. **Đọc dự án trước khi sửa:** kiểm tra `pubspec.yaml`, `lib/`, theme hiện tại, router/navigation, các màn hình, components/widgets tái sử dụng, assets, fonts, state management, animation đang có, các dependency và cấu trúc feature/module.
2. **Lập bản đồ UI:** liệt kê toàn bộ screen, luồng điều hướng, trạng thái `loading / empty / error / success`, bottom navigation, form, modal, dialog, list, feed, profile, chat, upload và các màn hình hiện thực sự có trong code. **Không giả định màn hình tồn tại**.
3. **Chụp baseline nếu môi trường cho phép:** chạy app hoặc Flutter widget/golden tests; lưu ảnh trước/sau các màn hình tiêu biểu. Nếu không có emulator, nêu rõ hạn chế và vẫn thực hiện kiểm chứng có thể chạy được.
4. **Thiết kế design system dùng chung trước:** tokens màu sắc, typography, spacing, radii, shadows, surfaces, component states, motion tokens, adaptive layout, accessibility và hỗ trợ light/dark.
5. **Refactor theo từng feature**, ưu tiên màn hình xuất hiện thường xuyên và các component dùng chung; không chỉnh sửa đại trà bằng thay thế text thiếu kiểm soát.
6. **Đảm bảo chức năng cũ không hỏng:** giữ nguyên API contracts, request/response mapping, repository, state management, authentication, validation, permission/roles, database models, routing semantics, localization và luồng nghiệp vụ, trừ khi sửa đúng một vấn đề UI gây lỗi và giải thích rõ.
7. **Tự chạy kiểm tra** phù hợp (`dart format`, `flutter analyze`, tests hiện có, build nếu có thể). Khắc phục lỗi do thay đổi gây ra.
8. **Báo cáo kết quả bằng file và nội dung ngắn:** các màn hình đã sửa, component mới, quyết định thiết kế, tác động performance, ảnh trước/sau nếu có, test đã chạy, tồn tại chưa hoàn thành.
9. **Không dừng ở đề xuất hay pseudocode.** Thực thi chỉnh sửa trực tiếp trên project; nếu phạm vi quá lớn, triển khai theo các đợt nhưng mỗi đợt phải có kết quả hoạt động được.

## 1. MỤC TIÊU CẢM NHẬN THỊ GIÁC

Ứng dụng phải đem lại cảm giác:

- **iOS premium:** bố cục gọn, sạch, có thứ bậc thị giác rõ; typography dễ đọc; thanh điều hướng nhẹ và nhất quán; chuyển cảnh mềm mại, tương tác chính xác.
- **Bright & fresh:** màu tươi nhưng không neon chói; nền sáng sạch; accent màu có chiến lược; sử dụng gradient tinh tế thay vì loang màu ở mọi nơi.
- **Soft & tactile:** góc bo lớn vừa phải, lớp kính mờ/translucent hợp lý, bóng đổ tự nhiên, các lớp nền nổi có chiều sâu.
- **Fluid motion:** tương tác phản hồi tức thì; micro-interactions có tính vật lý nhẹ, chuyển trạng thái theo nội dung, không nhảy giật.
- **3D-like depth:** parallax, perspective transform, layered cards, tilt và highlight động ở đúng điểm nhấn; không biến tất cả thành hoạt cảnh phô trương.
- **Content-first:** người dùng nhận ra nội dung và hành động chính trong 1–2 giây. Không hi sinh khả năng đọc và thao tác để chạy hiệu ứng.

**Không copy pixel-perfect giao diện của ứng dụng hoặc thương hiệu cụ thể.** Lấy cảm hứng từ Human Interface Guidelines và thẩm mỹ iOS nhưng duy trì nhận diện sản phẩm hiện có (logo, tên, domain/brand colors nếu đã được định nghĩa).

## 2. DESIGN SYSTEM — XÂY DỰNG TRƯỚC KHI SỬA CÁC SCREEN

### 2.1. Màu sắc (đề xuất khởi đầu, điều chỉnh theo brand hiện có)

**Light mode**:

| Token | Gợi ý màu | Vai trò |
|---|---|---|
| `background` | `#F7F9FC` | Nền chung |
| `surface` | `#FFFFFF` | Card, sheet, form |
| `surfaceSecondary` | `#EFF3FA` | Vùng phân cấp phụ |
| `primary` | `#336DFF` | Hành động chính, link |
| `primarySoft` | `#E9F0FF` | Selected state, nhấn nhẹ |
| `secondaryAccent` | `#61C9C3` | Điểm nhấn tươi mát |
| `tertiaryAccent` | `#FFA86C` | Điểm nhấn phụ có tiết chế |
| `textPrimary` | `#14223B` | Nội dung chính |
| `textSecondary` | `#65738C` | Metadata |
| `divider` | `#E5EAF2` | Ranh giới nhẹ |
| `success` | `#2DAF86` | Trạng thái thành công |
| `warning` | `#E5A23B` | Cảnh báo |
| `error` | `#DB5364` | Lỗi |

- Đây là **đề xuất**, không phải buộc phải đổi màu nếu app đã có brand palette. Trước tiên kiểm tra màu hiện có và ánh xạ sang semantic tokens.
- Tạo palette cho **dark mode** với contrast đủ dùng, không chỉ đảo màu tự động.
- Tránh dùng opacity tùy hứng rải rác; chuẩn hóa surface/overlay/border tokens.
- Tránh đặt gradient vào mọi card; chỉ dùng ở các hero surface hoặc vị trí spotlight.

### 2.2. Typography

- Ưu tiên font hệ thống theo từng nền tảng (cảm giác SF trên iOS), có fallback hỗ trợ tiếng Việt; **không phân phối hoặc nhúng font Apple độc quyền trái giấy phép**.
- Tổ chức type scale nhất quán, ví dụ: large title 30–34, screen title 24–28, section title 19–22, body 15–17, caption 12–14 logical pixels; điều chỉnh theo layout thực tế.
- Phân cấp bằng size/weight/spacing, không lạm dụng chữ đậm hay tất cả chữ in hoa.
- Hỗ trợ text scaling, tránh hardcode chiều cao khiến tiếng Việt bị cắt.

### 2.3. Spacing, radius, surface

- Spacing scale: `4 / 8 / 12 / 16 / 20 / 24 / 32 / 40`.
- Screen side padding mặc định 16–20; điều chỉnh trên tablet.
- Radius: chip 12–16; input 14–18; card 18–24; sheet 24–32 (theo use case).
- Border mảnh, shadow mềm với elevation nhẹ; tránh card nào cũng có bóng lớn.
- Mục tiêu minimum touch target khoảng **44×44 logical pixels** cho thao tác quan trọng.
- Safe areas, notch, home indicator, bàn phím, edge-to-edge phải xử lý đầy đủ.

### 2.4. Tạo các thành phần tái sử dụng (tùy cấu trúc dự án)

Không ép đặt tên/file nếu dự án đã có hệ thống tương đương. Cân nhắc:

- `AppTheme` / `AppColors` / `AppTypography` / `AppSpacing` / `AppRadii` / `AppMotion`
- `AppScaffold` / `AppNavigationBar` / `AppTabBar` / `AppTopBar`
- `AppPrimaryButton` / `AppSecondaryButton` / `AppIconButton`
- `AppTextField` / `AppSearchField` / `AppSegmentedControl`
- `AppCard` / `GlassSurface` / `ElevatedSurface` / `GradientHeroCard`
- `AppBottomSheet` / `AppDialog` / `AppToastOrBanner`
- `AppSkeleton` / `AppEmptyState` / `AppErrorState`
- `AnimatedLikeButton` / `AnimatedBookmarkButton` / `AnimatedCounter`
- `AppAvatar` / `AppBadge` / `AppChip` / `AppListTile`

**Không tạo abstractions không cần thiết**: chỉ tạo component khi dùng lặp lại hoặc giúp duy trì nhất quán.

## 3. iOS-INSPIRED NAVIGATION & UX

- Dùng top bar/large title/collapsing header phù hợp với màn hình; với iOS cân nhắc `CupertinoNavigationBar` hoặc `CupertinoSliverNavigationBar` ở nơi thích hợp.
- Bottom navigation/tab bar thanh thoát, khoảng chạm rõ; translucent/blur vừa đủ; animation icon/active indicator nhẹ.
- Transitions có tính liên tục không gian giữa list → detail, profile → content, card → full screen; hero chỉ khi có đối tượng chung rõ ràng.
- Sheet kéo lên mượt, bo góc, có drag handle hợp lý; hỗ trợ dismiss bằng gesture khi không gây mất dữ liệu.
- Back gesture, scroll physics, overscroll, keyboard dismissal, focus, validation và loading đều phải tự nhiên.
- Form: error inline rõ ràng, trạng thái nút submit đúng, focus order hợp lý, tự cuộn tới input bị lỗi, giữ dữ liệu khi chuyển bước.
- Haptic feedback nhẹ cho các hành động có ý nghĩa, tránh rung mọi lần cuộn/chạm; tương thích Android, có thể tắt được.
- Với các tác vụ nguy hiểm: có xác nhận; với thao tác có thể hoàn tác: ưu tiên Undo.
- Không để navigation/theme thành Cupertino thuần trên Android nếu gây hành vi lạ; mục tiêu là **iOS look & feel trên Flutter**, đồng thời tôn trọng gesture/accessibility của cả hai nền tảng.

## 4. ANIMATION & 3D — ĐẸP NHƯNG CÓ KIỂM SOÁT

### 4.1. Motion tokens (điểm bắt đầu, không phải thời lượng cứng)

| Nhóm | Khoảng thời gian tham khảo | Cảm giác |
|---|---:|---|
| Press / hover / feedback | 90–160 ms | Nhanh, chính xác |
| Toggle / icon / chip | 150–240 ms | Nhẹ, có chủ đích |
| Card entrance / list item | 220–360 ms | Mềm, không trễ |
| Page transition / sheet | 280–450 ms | Liền mạch |
| Hero / immersive detail | 350–650 ms | Ấn tượng nhưng không cản thao tác |

- Chọn `Curves.easeOutCubic`, `easeInOutCubic` hoặc mô hình spring phù hợp, tránh bounce quá đà.
- Scroll phải ưu tiên điều khiển trực tiếp của người dùng, không animation blocking.
- Stagger danh sách dùng rất tiết chế; không replay mỗi lần scroll gây rối.
- Animation luôn có trạng thái tĩnh hữu ích khi reduce motion được bật.

### 4.2. Hiệu ứng 3D / depth có thể triển khai

1. **Hero spotlight card:** layer nền gradient nhẹ, 2–3 lớp hình tạo chiều sâu, parallax nhỏ theo scroll/touch.
2. **Interactive tilt card:** `Transform` + `Matrix4` với perspective nhỏ, xoay trục X/Y giới hạn, shadow và highlight phản ứng khi chạm; tự trở về trạng thái phẳng khi thả.
3. **Shared element detail:** chuyển từ card sang detail bằng Hero/route transition, vẫn giữ layout ổn định.
4. **Floating decorative layers:** các shape/illustration có chuyển động rất nhẹ ở màn welcome/home; không ảnh hưởng nội dung.
5. **Glass-like bottom sheet / overlay:** chỉ blur vùng nhỏ, có fallback surface đặc khi cần và đảm bảo độ tương phản.
6. **Animated data feedback:** progress, skeleton shimmer mức độ thấp, nút like/save phản hồi bằng scale/color.

**Không bắt buộc dùng engine 3D**. Bắt đầu với Flutter `Transform`, `Animated*`, `AnimationController`, `Tween`, `Hero`, `CustomPainter` và `BackdropFilter` có chọn lọc. Chỉ cân nhắc Rive/Lottie hoặc thư viện 3D khi dự án thực sự cần và có asset phù hợp; giải thích trade-off về bundle size, battery và FPS.

### 4.3. Guardrails bắt buộc

- Không áp 3D cho ô nhập liệu, text nội dung dài, nút CTA cần đọc rõ, bảng biểu hoặc mọi item của danh sách lớn.
- Mỗi màn chỉ nên có **1 focal motion** và một số micro-interactions nhỏ.
- Avoid excessive blur, nested opacity layers, expensive shaders, continuous animations trên feed/chat.
- 3D tilt không làm content khó đọc, không lệch hit-testing, không gây motion sickness.
- Hỗ trợ `MediaQuery.disableAnimations`/nền tảng tương đương, tắt hoặc giảm parallax/tilt nếu hệ điều hành yêu cầu reduced motion.

## 5. ÁP DỤNG THEO CÁC NHÓM MÀN HÌNH CÓ THỰC TRONG PROJECT

**Đây là checklist định hướng, KHÔNG phải yêu cầu tạo thêm màn hình không có trong code.** Sau khi audit, map các mục dưới đây đến screen thực tế.

### 5.1. Onboarding / Login / Register
- Hero art/gradient êm, logo/brand rõ; form cân đối và keyboard-aware.
- Lỗi xác thực rõ; mật khẩu có toggle; nút CTA nổi bật, loading ổn định chiều rộng.
- Transition onboarding tinh tế, không kéo dài thời gian đăng nhập.

### 5.2. Home / Dashboard / Feed
- Large title hoặc welcome header mang cảm giác iOS.
- Nội dung chia block/hierarchy: section headers, featured surfaces, cards nhất quán.
- Nếu có feed: media chuẩn tỷ lệ, loading skeleton, like/comment/save animation nhỏ; scroll mượt.
- Nếu có bottom tabs: giữ tab state và scroll position khi đổi tab.

### 5.3. Groups / Community
- Group cover với depth nhẹ; avatar và thông tin nhóm rõ.
- Join/request state và role được hiển thị nhất quán, không thay đổi logic phân quyền.
- Feed nhóm / post detail / comments: spacing dễ đọc, action bar gọn, composer tránh bàn phím.

### 5.4. Document library / Study
- Subject filters, search và metadata rõ; card tài liệu có icon/preview dễ nhận diện.
- Upload workflow có progress, error, file validation feedback dễ hiểu.
- Trạng thái pending/approved/rejected hiển thị rõ nhưng không phô trương.

### 5.5. Chat / Messages
- Bubble spacing dễ đọc, timestamp và seen/delivered tinh tế.
- Composer responsive với keyboard, attachment tray mượt.
- Không chạy blur/shader/animation tốn kém trên toàn bộ danh sách tin nhắn.
- Giữ các luồng paging, realtime, unread đúng như hiện có.

### 5.6. AI Assistant / RAG (nếu có)
- Chat UI sạch, phân biệt câu hỏi/câu trả lời, trạng thái streaming, citation/source card.
- Citations dễ mở, không che khuất nội dung.
- Empty state có gợi ý câu hỏi; typing animation chỉ khi hữu ích.

### 5.7. Profile / Settings
- Header avatar + cover được trình bày đẹp, phân cấp thông tin rõ.
- Settings nhóm theo section dạng iOS; toggle/segmented control/dialog nhất quán.
- Đảm bảo accessibility, logout, confirmation và trạng thái private data.

## 6. CHẤT LƯỢNG UX / ACCESSIBILITY / PERFORMANCE

- Responsive cho điện thoại nhỏ, lớn; portrait trước, landscape/tablet nếu project có hỗ trợ.
- Không overflow hoặc text clipping khi text scale lớn, tiếng Việt dài hay keyboard mở.
- WCAG contrast phù hợp: mục tiêu >=4.5:1 cho văn bản thông thường; ít nhất tương phản rõ cho icon/action.
- Semantics labels cho icon-only controls, screen reader focus order, trạng thái chọn, error message.
- Gesture không xung đột với nested scroll, back swipe, dismiss sheet.
- `const` và rebuild scope hợp lý; lazy list (`ListView.builder`/slivers), image cache, resize image và placeholders.
- Đặt `RepaintBoundary` có cân nhắc; tránh implicit animations trên list lớn hoặc quá nhiều frame redraw.
- Mục tiêu trải nghiệm 60 FPS trên thiết bị mục tiêu; nếu 120Hz có sẵn, tối ưu nhưng không hy sinh pin.
- Profile bằng Flutter DevTools (Performance/Timeline) nếu có môi trường; ghi nhận frame build/raster bất thường.
- Mỗi trạng thái loading/error/empty/offline phải đẹp và có hành động tiếp theo rõ ràng.
- Hạn chế thêm package không cần thiết; ưu tiên Flutter SDK. Nếu thêm dependency, giải thích lý do, license và overhead.

## 7. NGUYÊN TẮC BẢO TOÀN DỰ ÁN

**Không được:**
- Viết lại toàn bộ app từ đầu hoặc thay đổi kiến trúc module mà không có lý do chắc chắn.
- Xóa/sửa backend, API routes, database schema, auth flow, permission roles, RAG logic, data validation.
- Đổi tên public classes/functions/route names gây break các nơi đang dùng mà không migrate đầy đủ.
- Thay đổi text nghiệp vụ, dữ liệu, localization chỉ vì muốn demo UI.
- Thêm hardcoded mock data thay cho dữ liệu API đang có.
- Bỏ qua dark mode, SafeArea, keyboard, accessibility.
- Sử dụng animation/3D quá nhiều khiến app giật lag.
- Tạo code không chạy rồi tuyên bố hoàn thành.

**Nên làm:**
- Làm việc trên nhánh riêng nếu có Git; kiểm tra `git status` trước khi sửa, không overwrite thay đổi chưa commit.
- Giữ nguyên state management hiện có (Bloc, Riverpod, Provider, GetX, v.v.) trừ khi có nguyên nhân cụ thể cần sửa.
- Dùng adaptive widgets khi thực sự hữu ích thay vì phối trộn Material/Cupertino thiếu nhất quán.
- Áp dụng `ThemeExtension` hoặc kiến trúc token tương đương để theme nhất quán.
- Reuse feature widgets và routing patterns sẵn có.

## 8. PHASED EXECUTION PLAN — PHẢI THỰC THI

### Phase A — Audit & Blueprint
1. Đọc source, liệt kê màn hình và thành phần UI hiện hữu.
2. Xác định 5–10 điểm làm app hiện giống Android/Material mặc định (AppBar, Button, Dialog, Nav, Card, Animation...).
3. Đưa ra bảng mapping `Hiện tại → Thiết kế mới → File cần sửa`.
4. Xác định component/theme nào cần tái sử dụng; ưu tiên thay đổi ít rủi ro.

### Phase B — Foundation
1. Tạo semantic theme tokens, light/dark và typography.
2. Hoàn thiện button, input, card, navbar, sheet, feedback states.
3. Tạo motion presets và utility cho reduced motion.
4. Xây dựng demo/preview hoặc widget tests cho các component then chốt nếu khả thi.

### Phase C — High-impact Screens
1. Refactor home/feed và navigation trước.
2. Refactor auth, profile và một màn detail quan trọng.
3. Dùng Hero/parallax/tilt cho một khu vực spotlight có lợi ích rõ ràng.
4. Kiểm tra UI trực tiếp sau từng nhóm thay đổi; tránh các màn hình mỗi nơi một style.

### Phase D — Feature Coverage
1. Tiếp tục các screen thực có: groups, documents, chat, AI assistant, settings, upload/moderation, v.v.
2. Áp dụng đủ trạng thái UI (`loading`, `empty`, `error`, `success`), animation nhỏ, accessibility.
3. Kiểm tra giao diện khi dữ liệu thật dài/thiếu/bất thường.

### Phase E — QA & Polish
1. `dart format .` hoặc theo phạm vi file đã sửa.
2. `flutter analyze` và khắc phục lỗi phát sinh.
3. `flutter test` nếu project có test.
4. Build/run trên target có sẵn (ưu tiên iOS simulator khi có macOS/Xcode; Android emulator làm kiểm tra chéo).
5. Kiểm thử dark mode, small screen, safe area, keyboard, text scale, reduce motion, low-end frame pacing.
6. Nếu thiếu môi trường iOS, nêu rõ chưa xác nhận runtime iOS; **không báo đã test nếu chưa chạy**.

## 9. ACCEPTANCE CRITERIA — ĐIỀU KIỆN HOÀN THÀNH

- [ ] Các màn hình hiện có được audit và có phạm vi thay đổi rõ ràng.
- [ ] Thiết kế có ngôn ngữ iOS-inspired nhất quán, rõ ràng, tươi sáng, mềm mại.
- [ ] Có theme tokens và các component dùng chung; hạn chế hardcoded style.
- [ ] Navigation, button, input, card, modal, tab bar và loading states đồng bộ.
- [ ] Có micro-interactions và ít nhất một ví dụ depth/3D chất lượng tại điểm nhấn phù hợp **nếu project có khu vực phù hợp**.
- [ ] Chuyển cảnh mượt, không xung đột gesture/scroll/keyboard.
- [ ] Có hỗ trợ giảm chuyển động, accessibility và dark mode (nếu app cho phép).
- [ ] Không phá API, dữ liệu, phân quyền, chức năng và các luồng đang chạy.
- [ ] `flutter analyze` và test/build áp dụng được chạy, kết quả được báo trung thực.
- [ ] Có tóm tắt file đã sửa và các vấn đề còn lại.

## 10. KẾT QUẢ CODEX PHẢI TRẢ VỀ

**A. Trước khi sửa:**
- Danh sách screen + navigation + widget/component chung được tìm thấy.
- Kế hoạch thay đổi các file và style direction theo dự án thực tế.

**B. Trong khi sửa:**
- Sửa code thực tế theo phases; báo phần nào xong và phần nào tiếp tục.
- Duy trì app chạy được sau từng phase.

**C. Khi hoàn thành:**
- Liệt kê file tạo mới/sửa đổi.
- Tóm tắt thay đổi UI/UX theo màn hình.
- Chỉ rõ các animation/3D đã thực sự triển khai và nơi sử dụng.
- Kết quả format/analyze/test/build (pass/fail/not run và nguyên nhân).
- Các screenshot trước/sau nếu đã chạy được app.
- Những việc chưa làm, rủi ro còn lại, hướng test trên iPhone thực tế.

---

## 11. LỆNH BẮT ĐẦU NGAY CHO CODEX

> Hãy bắt đầu bằng cách **audit code Flutter hiện có** trong repository này. Đọc cấu trúc modules, routing, theme, common widgets và các màn hình, sau đó trình bày ngắn bản đồ UI cùng kế hoạch chỉnh sửa cụ thể. **Tiếp theo tiến hành sửa code ngay, không dừng ở bản kế hoạch**. Ưu tiên thay hệ thống theme/components, bottom navigation, home/feed và các luồng tương tác chính để ứng dụng chuyển rõ từ giao diện Material/Android mặc định sang trải nghiệm iOS-inspired premium: sáng, mượt, mềm, màu tươi, chuyển cảnh chất lượng, hiệu ứng 3D tinh tế. Tuyệt đối bảo toàn logic nghiệp vụ hiện có. Xong mỗi phase hãy chạy các kiểm tra khả thi, sửa lỗi phát sinh và tiếp tục triển khai đến khi phủ các màn hình thực có trong dự án. Báo cáo trung thực kết quả cuối cùng.
