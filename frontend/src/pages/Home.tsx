import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Bell,
  Box,
  Camera,
  FileText,
  Heart,
  Leaf,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import { useStore } from "../store";
import { CountUp, ItemCard, StatCard } from "../components/ui";
import ProductImage from "../components/ProductImage";
import { ITEM_ASSETS } from "../assets/itemAssets";
export default function Home() {
  const data = useStore((s) => s.data)!;
  const [slide, setSlide] = useState(0);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const reduce = useReducedMotion();
  useEffect(() => {
    if (reduce) return;
    const t = setInterval(() => setSlide((v) => (v + 1) % 4), 4200);
    return () => clearInterval(t);
  }, [reduce]);
  const features = [
    ["拍照识别建档", "多图识别，少填一些", "/items/new", Camera, "green"],
    ["退换保修提醒", "重要时间，不再错过", "/reminders", Bell, "orange"],
    ["说明书随手查", "物品资料，安放有序", "/items/headphones", FileText, "blue"],
    ["维护与维修", "记录每一次认真照顾", "/repairs", Wrench, "green"],
    ["耗材补给预测", "从历史推算补给时间", "/consumables", Box, "purple"],
    ["物品专属助手", "带着档案，回答问题", "/assistant", Sparkles, "purple"],
  ] as const;
  const slides = [
    "每件物品，都有自己的故事",
    "保修有期限，安心有提醒",
    "一点点维护，陪伴更长久",
    "耗材快用完，补给早一点",
  ];
  return (
    <div className="home-page">
      <section
        className="hero"
        onMouseMove={(e) => {
          if (!reduce) {
            const rect = e.currentTarget.getBoundingClientRect();
            setMouse({
              x: ((e.clientX - rect.left - rect.width / 2) / rect.width) * 12,
              y: ((e.clientY - rect.top - rect.height / 2) / rect.height) * 12,
            });
          }
        }}
      >
        <div
          aria-hidden="true"
          className="hero-leaves"
          style={{ transform: `translate(${mouse.x}px,${mouse.y}px)` }}
        />
        <div className="hero-copy">
          <h1>
            让每一件物品，
            <br />
            都被<span>好好对待</span>
          </h1>
          <p>
            物生是一款面向家庭与个人的 AI
            物品生命周期管理平台，帮助你管理购买、退换、保修、说明书、维护、维修与耗材补给。
          </p>
          <div className="hero-actions">
            <Link className="button primary" to="/items">
              立即体验
              <ArrowRight size={19} />
            </Link>
            <a className="button secondary" href="#features">
              查看功能
            </a>
          </div>
        </div>
        <div className="hero-demo-wrap">
          <motion.div
            className="hero-demo"
            animate={reduce ? {} : { y: [0, -5, 0] }}
            transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
          >
            <div className="demo-chrome">
              <span className="demo-brand">
                <Leaf size={17} />
                物生 <small>Wusheng</small>
              </span>
              <span>本地演示数据</span>
              <Link to="/items/new">
                <Plus /> 添加物品
              </Link>
            </div>
            <div className="demo-inner">
              <div className="demo-sidebar">
                <HomeIcon />
                首页
                <PackageIcon />
                物品
                <Bell size={15} />
                提醒
                <Box size={15} />
                耗材
                <Sparkles size={15} />
                助手
              </div>
              <div className="demo-content">
                <div className="demo-stats">
                  <StatCard label="全部物品" value={data.stats.itemCount} />
                  <StatCard label="保修中" value={data.stats.warrantyCount} icon={ShieldCheck} />
                  <StatCard
                    label="待维护"
                    value={data.stats.maintenanceDue}
                    icon={Wrench}
                    tone="orange"
                  />
                </div>
                <div className="demo-tabs">
                  <span>全部</span>家电 数码 家居
                </div>
                <div className="demo-items">
                  {data.items.slice(0, 3).map((item) => (
                    <ItemCard key={item.id} item={item} priority />
                  ))}
                </div>
                <AnimatePresence mode="wait">
                  <motion.div
                    className={`demo-message state-${slide}`}
                    key={slide}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                  >
                    <span className="live-dot" />
                    {slides[slide]}
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
          <div className="demo-dots">
            {slides.map((_, i) => (
              <button
                key={i}
                className={i === slide ? "active" : ""}
                aria-label={`展示第${i + 1}个状态`}
                onClick={() => setSlide(i)}
              />
            ))}
          </div>
        </div>
      </section>
      <section id="features" className="feature-strip">
        {features.map(([title, text, to, Icon, tone]) => (
          <Link className="feature" to={to} key={title}>
            <span className={`icon-well ${tone}`}>
              <Icon size={25} />
            </span>
            <div>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
            <ChevronArrow />
          </Link>
        ))}
      </section>
      <section className="home-section">
        <header>
          <h2>生活里的物品，值得被记住</h2>
        </header>
        <div className="scene-grid">
          {[
            ["家庭家电管理", "购买、保修与维护，都有迹可循", "washer", "家电"],
            ["数码设备管理", "让每一次陪伴，延续得久一点", "laptop", "数码"],
            ["日常耗材管理", "用得安心，补给刚刚好", "toothbrush", "耗材"],
          ].map(([title, desc, img, category]) => (
            <Link
              key={title}
              className="scene"
              to={category === "耗材" ? "/consumables" : `/items?category=${category}`}
            >
              <ProductImage src={ITEM_ASSETS[img].src} alt="" />
              <div>
                <h3>{title}</h3>
                <p>{desc}</p>
              </div>
              <ArrowRight />
            </Link>
          ))}
        </div>
      </section>
      <section className="home-section steps-section">
        <header>
          <h2>简单四步，轻松照顾每一件物品</h2>
          <span className="demo-total">
            目前记录 <CountUp value={data.stats.itemCount} /> 件物品
          </span>
        </header>
        <div className="home-steps">
          {[
            ["上传图片", "照片、小票或包装盒", Camera],
            ["识别并确认", "每个字段都有来源", Sparkles],
            ["建立档案", "记录物品的生命周期", FileText],
            ["安心使用", "维护与补给及时提醒", Heart],
          ].map(([title, desc, Icon], i) => {
            const I = Icon as typeof Camera;
            return (
              <div key={String(title)}>
                <span className="step-number">{i + 1}</span>
                <I size={30} />
                <section>
                  <b>{String(title)}</b>
                  <p>{String(desc)}</p>
                </section>
                {i < 3 && <ArrowRight className="step-arrow" />}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
function Plus() {
  return <span>＋</span>;
}
function ChevronArrow() {
  return <ArrowRight size={15} />;
}
function HomeIcon() {
  return <Leaf size={15} />;
}
function PackageIcon() {
  return <Box size={15} />;
}
