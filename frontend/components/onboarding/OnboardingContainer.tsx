"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const slides = [
    {
        kind: "splash",
        title: "HVNH Hub",
        description: "",
    },
    {
        kind: "news",
        title: "Cập nhật các tin tức mới nhất",
        description: "Các tin tức mới nhất sẽ được cập nhật liên tục trên ứng dụng",
    },
    {
        kind: "market",
        title: "Mua bán, trao đổi đồ dùng",
        description:
            "Cho phép sinh viên mua bán, trao đổi đồ dùng trên ứng dụng trực tuyến",
    },
    {
        kind: "study",
        title: "Chia sẻ, tìm kiếm tài liệu học tập",
        description:
            "Các kiến thức, tài liệu học tập sẽ được chia sẻ giữa các sinh viên trong trường",
    },
    {
        kind: "roommate",
        title: "Tìm kiếm bạn ở cùng",
        description:
            "Kết nối với các sinh viên có cùng nhu cầu về phòng ở trong trường học",
    },
] as const;

const avatarSeeds = ["Mai", "Nam", "Linh", "Khanh", "An", "Tuan"];

function OnboardingProgress({
    current,
    onSelect,
}: {
    current: number;
    onSelect: (index: number) => void;
}) {
    return (
        <div className="onboarding-progress" aria-label="Tiến trình giới thiệu">
            {slides.map((slide, index) => (
                <button
                    key={slide.kind}
                    className={
                        index === current ? "progress-step active" : "progress-step"
                    }
                    type="button"
                    aria-label={`Chuyển tới màn hình ${index + 1}`}
                    aria-current={index === current ? "step" : undefined}
                    onClick={() => onSelect(index)}
                />
            ))}
        </div>
    );
}

function AvatarOrbit({ kind }: { kind: string }) {
    if (kind === "splash") {
        return (
            <div className="splash-mark-wrap" aria-label="Logo BAV">
                <div className="bav-mark">
                    <strong>BAV</strong>
                    <span>✦</span>
                    <small>1961</small>
                </div>
            </div>
        );
    }

    const heroSeed =
        kind === "news"
            ? "Mai"
            : kind === "market"
                ? "Nam"
                : kind === "study"
                    ? "Linh"
                    : "Khanh";
    return (
        <div className={`orbit orbit-${kind}`} aria-hidden="true">
            <div className="orbit-hero">
                <img
                    src={`https://api.dicebear.com/9.x/fun-emoji/svg?seed=${heroSeed}`}
                    alt=""
                />
            </div>
            {avatarSeeds.map((seed, index) => (
                <span className={`orbit-avatar orbit-avatar-${index}`} key={seed}>
                    <img
                        src={`https://api.dicebear.com/9.x/fun-emoji/svg?seed=${seed}`}
                        alt=""
                    />
                </span>
            ))}
        </div>
    );
}

function Splash({
    onContinue,
    onSelect,
}: {
    onContinue: () => void;
    onSelect: (index: number) => void;
}) {
    return (
        <section className="onboarding-screen splash-screen">
            <span className="orange-orb orb-top" aria-hidden="true" />
            <span className="orange-orb orb-middle" aria-hidden="true" />
            <span className="orange-orb orb-bottom" aria-hidden="true" />
            <div className="splash-content">
                <AvatarOrbit kind="splash" />
                <h1>HVNH Hub</h1>
            </div>
            <button
                className="onboarding-primary splash-button"
                type="button"
                onClick={onContinue}
            >
                Tiếp tục
            </button>
            <OnboardingProgress current={0} onSelect={onSelect} />
        </section>
    );
}

function OnboardingSlide({
    index,
    onContinue,
    onSkip,
    onSelect,
}: {
    index: number;
    onContinue: () => void;
    onSkip: () => void;
    onSelect: (index: number) => void;
}) {
    const slide = slides[index];
    return (
        <section className="onboarding-screen slide-screen">
            <div className="slide-visual">
                <AvatarOrbit kind={slide.kind} />
            </div>
            <div className="slide-copy">
                <h1>{slide.title}</h1>
                <p>{slide.description}</p>
            </div>
            <div className="onboarding-actions">
                <button
                    className="onboarding-primary"
                    type="button"
                    onClick={onContinue}
                >
                    Tiếp tục
                </button>
                {index < slides.length - 1 ? (
                    <button
                        className="onboarding-secondary"
                        type="button"
                        onClick={onSkip}
                    >
                        Bỏ qua
                    </button>
                ) : null}
            </div>
            <p className="login-prompt">
                Đã có tài khoản? <Link href="/login">Đăng nhập</Link>
            </p>
            <OnboardingProgress current={index} onSelect={onSelect} />
        </section>
    );
}

export default function OnboardingContainer() {
    const [index, setIndex] = useState(0);
    const router = useRouter();

    function skipToSignup() {
        router.push("/signup");
    }

    function continueFromOnboarding() {
        if (index === slides.length - 1) {
            router.push("/signup");
            return;
        }
        setIndex(index + 1);
    }

    if (index === 0) {
        return <Splash onContinue={() => setIndex(1)} onSelect={setIndex} />;
    }

    return (
        <OnboardingSlide
            index={index}
            onContinue={continueFromOnboarding}
            onSkip={skipToSignup}
            onSelect={setIndex}
        />
    );
}
