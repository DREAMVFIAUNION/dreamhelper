import dynamic from 'next/dynamic'
import { HeroSection } from '@/components/landing/HeroSection'
import { TrustBar } from '@/components/landing/TrustBar'
import { FeaturesSection } from '@/components/landing/FeaturesSection'

const SkillsShowcase = dynamic(() => import('@/components/landing/SkillsShowcase').then(m => ({ default: m.SkillsShowcase })))
const ProductPreview = dynamic(() => import('@/components/landing/ProductPreview').then(m => ({ default: m.ProductPreview })))
const StatsSection = dynamic(() => import('@/components/landing/StatsSection').then(m => ({ default: m.StatsSection })))
const PricingSection = dynamic(() => import('@/components/landing/PricingSection').then(m => ({ default: m.PricingSection })))
const TestimonialsSection = dynamic(() => import('@/components/landing/TestimonialsSection').then(m => ({ default: m.TestimonialsSection })))
const FAQSection = dynamic(() => import('@/components/landing/FAQSection').then(m => ({ default: m.FAQSection })))
const CTASection = dynamic(() => import('@/components/landing/CTASection').then(m => ({ default: m.CTASection })))

export default function LandingPage() {
  return (
    <>
      <HeroSection />
      <TrustBar />
      <FeaturesSection />
      <SkillsShowcase />
      <ProductPreview />
      <StatsSection />
      <PricingSection />
      <TestimonialsSection />
      <FAQSection />
      <CTASection />
    </>
  )
}
