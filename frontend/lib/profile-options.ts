export const HVNH_SCHOOL_NAME = 'Học viện Ngân hàng (BAV)';

export const HVNH_FACULTIES = [
  'Khoa Ngân hàng',
  'Khoa Tài chính',
  'Khoa Kế toán - Kiểm toán',
  'Khoa Quản trị kinh doanh',
  'Khoa Kinh doanh quốc tế',
  'Khoa Công nghệ thông tin và Kinh tế số',
  'Khoa Ngoại ngữ',
  'Khoa Luật',
  'Khoa Kinh tế',
  'Viện Đào tạo quốc tế',
] as const;

export const VIETNAM_PROVINCES = [
  'Hà Nội', 'Cao Bằng', 'Tuyên Quang', 'Điện Biên', 'Lai Châu', 'Sơn La',
  'Lào Cai', 'Thái Nguyên', 'Lạng Sơn', 'Quảng Ninh', 'Bắc Ninh', 'Phú Thọ',
  'Hải Phòng', 'Hưng Yên', 'Ninh Bình', 'Thanh Hóa', 'Nghệ An', 'Hà Tĩnh',
  'Quảng Trị', 'Huế', 'Đà Nẵng', 'Quảng Ngãi', 'Gia Lai', 'Khánh Hòa',
  'Đắk Lắk', 'Lâm Đồng', 'Đồng Nai', 'Thành phố Hồ Chí Minh', 'Tây Ninh',
  'Đồng Tháp', 'Vĩnh Long', 'An Giang', 'Cần Thơ', 'Cà Mau',
] as const;

export function deriveCourseYear(studentCode?: string): string {
  const match = studentCode?.trim().match(/^(\d{2})/);
  if (!match) return '';
  const cohort = Number(match[1]);
  if (cohort < 18 || cohort > 60) return '';
  const startYear = 1997 + cohort;
  return `K${cohort} (${startYear}-${startYear + 4})`;
}

export function normalizeSocialUrl(value: string): string {
  const trimmed = value.trim();
  if (!trimmed || /^https?:\/\//i.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}
