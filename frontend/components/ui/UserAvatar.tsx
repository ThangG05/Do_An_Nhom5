"use client";

import { useEffect, useState } from "react";

interface UserAvatarProps {
  src?: string | null;
  name?: string | null;
  alt?: string;
  imageClassName?: string;
  fallbackClassName?: string;
}

function initialsOf(name?: string | null) {
  const parts = (name || "Người dùng").trim().split(/\s+/).filter(Boolean);
  return parts.slice(-2).map((part) => part[0]).join("").toUpperCase() || "U";
}

export default function UserAvatar({ src, name, alt, imageClassName, fallbackClassName }: UserAvatarProps) {
  const normalizedSource = src?.trim() || "";
  const [failed, setFailed] = useState(false);

  useEffect(() => setFailed(false), [normalizedSource]);

  if (!normalizedSource || failed) {
    return (
      <span className={fallbackClassName} role="img" aria-label={alt || `Ảnh đại diện của ${name || "người dùng"}`}>
        {initialsOf(name)}
      </span>
    );
  }

  return <img src={normalizedSource} alt={alt || `Ảnh đại diện của ${name || "người dùng"}`} className={imageClassName} onError={() => setFailed(true)} />;
}
