"use client";

import { useRef, useState } from "react";
import styles from "./CommunityUniverse.module.css";

const spaces = [
  { name: "Học tập", icon: "▤", color: "#86baff", detail: "Chia sẻ tài liệu. Cùng nhau tiến bộ." },
  { name: "Sự kiện", icon: "✦", color: "#ffd483", detail: "Khám phá hoạt động. Tạo thêm kỷ niệm." },
  { name: "Pass đồ", icon: "♧", color: "#ffa4ca", detail: "Trao lại món đồ. Nối dài giá trị." },
  { name: "Ghép phòng", icon: "⌂", color: "#85e1c0", detail: "Tìm chốn ở mới. Gặp người bạn mới." },
];

export default function CommunityUniverse() {
  const scene = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState(0);
  const [paused, setPaused] = useState(false);
  const reset = () => {
    scene.current?.style.setProperty("--look-x", "0deg");
    scene.current?.style.setProperty("--look-y", "0deg");
  };
  return <div className={styles.universe} data-paused={paused} style={{ "--space-color": spaces[selected].color } as React.CSSProperties}>
    <div className={styles.scene} ref={scene} onPointerMove={event => {
      if (event.pointerType !== "mouse" || paused || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const rect = event.currentTarget.getBoundingClientRect();
      scene.current?.style.setProperty("--look-x", `${-(event.clientY - rect.top - rect.height / 2) / rect.height * 9}deg`);
      scene.current?.style.setProperty("--look-y", `${(event.clientX - rect.left - rect.width / 2) / rect.width * 12}deg`);
    }} onPointerLeave={reset}>
      <div className={styles.grid} aria-hidden="true" />
      <div className={styles.world}>
        <div className={styles.orbit} aria-hidden="true"><i /><i /></div>
        <div className={`${styles.orbit} ${styles.orbitSecond}`} aria-hidden="true"><i /></div>
        <div className={styles.core} aria-hidden="true">
          <div className={styles.sphere}><img src="/assets/logo.png" alt="" /><strong>HVNH<span>HUB</span></strong></div>
          <div className={styles.pedestal} />
        </div>
        <div className={styles.cards} role="group" aria-label="Khám phá bốn hội nhóm">
          {spaces.map((space, index) => <button key={space.name} type="button" className={styles.card} data-slot={index} aria-pressed={selected === index} onClick={() => setSelected(index)} style={{ "--card-color": space.color } as React.CSSProperties}>
            <span className={styles.icon} aria-hidden="true">{space.icon}</span><span><small>KHÔNG GIAN KẾT NỐI</small><b>{space.name}</b></span><span className={styles.arrow} aria-hidden="true">↗</span>
          </button>)}
        </div>
        <span className={styles.star} aria-hidden="true">✧</span>
        <span className={styles.starTwo} aria-hidden="true">✦</span>
      </div>
    </div>
    <div className={styles.caption}>
      <div aria-live="polite"><strong>{spaces[selected].name}</strong><p>{spaces[selected].detail}</p></div>
      <button type="button" onClick={() => { setPaused(value => !value); reset(); }} aria-label={paused ? "Bật chuyển động minh họa" : "Tạm dừng chuyển động minh họa"} aria-pressed={paused}>{paused ? "▷" : "Ⅱ"}</button>
    </div>
    <p className={styles.hint}>Chạm vào một hội nhóm để khám phá</p>
  </div>;
}
