/**
 * Community Center Panel
 * Marketplace for Tools, MCPs, and Agents
 * Features: Browse, Import, Submit, Ratings, Comments
 * Monetization: Verified/Premium paid content with revenue sharing
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  StarIcon,
  ArrowDownTrayIcon,
  ChatBubbleLeftRightIcon,
  CheckBadgeIcon,
  SparklesIcon,
  CurrencyDollarIcon,
  TrophyIcon,
  UserGroupIcon,
  CodeBracketIcon,
  ServerIcon,
  CpuChipIcon,
  HeartIcon,
  ShareIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid, HeartIcon as HeartIconSolid } from '@heroicons/react/24/solid';

interface CommunityCenterPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'explore' | 'my-items' | 'submit';
type CategoryType = 'all' | 'tool' | 'mcp' | 'agent';
type SortType = 'trending' | 'popular' | 'recent' | 'top-rated';

interface MarketplaceItem {
  id: string;
  type: 'tool' | 'mcp' | 'agent';
  name: string;
  description: string;
  author: {
    name: string;
    username: string;
    avatar: string;
    verified: boolean;
  };
  stats: {
    downloads: number;
    rating: number;
    reviews: number;
    favorites: number;
  };
  pricing: {
    type: 'free' | 'paid';
    price?: number;
    revenueShare?: number; // Percentage to developer
  };
  tags: string[];
  verified: boolean;
  premium: boolean;
  featured: boolean;
  createdAt: string;
  updatedAt: string;
}

interface Comment {
  id: string;
  author: {
    name: string;
    username: string;
    avatar: string;
  };
  content: string;
  rating: number;
  createdAt: string;
  replies: Comment[];
}

// Mock data
const mockItems: MarketplaceItem[] = [
  {
    id: '1',
    type: 'tool',
    name: 'Advanced Web Scraper Pro',
    description: 'Professional-grade web scraping with JavaScript rendering, anti-bot bypass, and proxy rotation. Handles SPAs, pagination, and complex workflows.',
    author: {
      name: 'WebMaster AI',
      username: 'webmaster_ai',
      avatar: 'WA',
      verified: true,
    },
    stats: {
      downloads: 12534,
      rating: 4.9,
      reviews: 234,
      favorites: 1823,
    },
    pricing: {
      type: 'paid',
      price: 29.99,
      revenueShare: 70,
    },
    tags: ['scraping', 'automation', 'javascript', 'professional'],
    verified: true,
    premium: true,
    featured: true,
    createdAt: '2024-09-15',
    updatedAt: '2024-10-05',
  },
  {
    id: '2',
    type: 'mcp',
    name: 'Stripe Payment Gateway',
    description: 'Complete Stripe integration with subscription management, webhooks, and invoice handling. Full visual configuration.',
    author: {
      name: 'Payment Guru',
      username: 'payment_guru',
      avatar: 'PG',
      verified: true,
    },
    stats: {
      downloads: 8342,
      rating: 5.0,
      reviews: 189,
      favorites: 1456,
    },
    pricing: {
      type: 'paid',
      price: 49.99,
      revenueShare: 70,
    },
    tags: ['payments', 'stripe', 'subscriptions', 'enterprise'],
    verified: true,
    premium: true,
    featured: true,
    createdAt: '2024-08-20',
    updatedAt: '2024-10-01',
  },
  {
    id: '3',
    type: 'agent',
    name: 'SEO Content Optimizer',
    description: 'Complete workflow with research, content generation, and optimization. Includes 3 specialized agents working in harmony.',
    author: {
      name: 'SEO Specialist',
      username: 'seo_specialist',
      avatar: 'SS',
      verified: false,
    },
    stats: {
      downloads: 15234,
      rating: 4.8,
      reviews: 456,
      favorites: 2103,
    },
    pricing: {
      type: 'free',
    },
    tags: ['seo', 'content', 'marketing', 'multi-agent'],
    verified: false,
    premium: false,
    featured: true,
    createdAt: '2024-07-10',
    updatedAt: '2024-09-28',
  },
  {
    id: '4',
    type: 'tool',
    name: 'Email Campaign Manager',
    description: 'Send bulk emails, track opens/clicks, manage templates, and automate follow-ups. Integrates with major email providers.',
    author: {
      name: 'Email Pro',
      username: 'email_pro',
      avatar: 'EP',
      verified: true,
    },
    stats: {
      downloads: 6789,
      rating: 4.7,
      reviews: 123,
      favorites: 892,
    },
    pricing: {
      type: 'paid',
      price: 19.99,
      revenueShare: 70,
    },
    tags: ['email', 'marketing', 'automation', 'campaigns'],
    verified: true,
    premium: true,
    featured: false,
    createdAt: '2024-09-01',
    updatedAt: '2024-10-08',
  },
  {
    id: '5',
    type: 'mcp',
    name: 'Google Workspace Suite',
    description: 'Complete Google Workspace integration: Gmail, Drive, Docs, Sheets, Calendar. Full CRUD operations.',
    author: {
      name: 'Cloud Connect',
      username: 'cloud_connect',
      avatar: 'CC',
      verified: false,
    },
    stats: {
      downloads: 4521,
      rating: 4.6,
      reviews: 87,
      favorites: 634,
    },
    pricing: {
      type: 'free',
    },
    tags: ['google', 'workspace', 'productivity', 'cloud'],
    verified: false,
    premium: false,
    featured: false,
    createdAt: '2024-08-15',
    updatedAt: '2024-09-20',
  },
  {
    id: '6',
    type: 'agent',
    name: 'Financial Analysis Bot',
    description: 'Analyze financial statements, generate reports, and provide investment insights. Includes market data integration.',
    author: {
      name: 'FinTech AI',
      username: 'fintech_ai',
      avatar: 'FA',
      verified: true,
    },
    stats: {
      downloads: 3456,
      rating: 4.9,
      reviews: 91,
      favorites: 723,
    },
    pricing: {
      type: 'paid',
      price: 99.99,
      revenueShare: 70,
    },
    tags: ['finance', 'analysis', 'investing', 'professional'],
    verified: true,
    premium: true,
    featured: false,
    createdAt: '2024-07-25',
    updatedAt: '2024-10-02',
  },
];

const mockComments: Record<string, Comment[]> = {
  '1': [
    {
      id: 'c1',
      author: {
        name: 'John Developer',
        username: 'john_dev',
        avatar: 'JD',
      },
      content: 'This is hands down the best scraping tool I\'ve used! The anti-bot detection works flawlessly. Worth every penny.',
      rating: 5,
      createdAt: '2024-10-08',
      replies: [
        {
          id: 'c1r1',
          author: {
            name: 'WebMaster AI',
            username: 'webmaster_ai',
            avatar: 'WA',
          },
          content: 'Thanks for the feedback! We\'re constantly improving the anti-bot algorithms.',
          rating: 0,
          createdAt: '2024-10-09',
          replies: [],
        },
      ],
    },
    {
      id: 'c2',
      author: {
        name: 'Sarah Smith',
        username: 'sarah_s',
        avatar: 'SS',
      },
      content: 'Great tool but the documentation could be better. Took me a while to figure out proxy rotation.',
      rating: 4,
      createdAt: '2024-10-05',
      replies: [],
    },
  ],
};

export const CommunityCenterPanel: React.FC<CommunityCenterPanelProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<TabType>('explore');
  const [selectedCategory, setSelectedCategory] = useState<CategoryType>('all');
  const [selectedSort, setSelectedSort] = useState<SortType>('trending');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItem, setSelectedItem] = useState<MarketplaceItem | null>(null);
  const [showComments, setShowComments] = useState(false);

  // Filter items
  const filteredItems = mockItems.filter((item) => {
    if (selectedCategory !== 'all' && item.type !== selectedCategory) return false;
    if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !item.description.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  // Sort items
  const sortedItems = [...filteredItems].sort((a, b) => {
    switch (selectedSort) {
      case 'trending':
        return b.stats.downloads - a.stats.downloads;
      case 'popular':
        return b.stats.favorites - a.stats.favorites;
      case 'top-rated':
        return b.stats.rating - a.stats.rating;
      case 'recent':
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      default:
        return 0;
    }
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'tool':
        return <CodeBracketIcon className="w-5 h-5" />;
      case 'mcp':
        return <ServerIcon className="w-5 h-5" />;
      case 'agent':
        return <CpuChipIcon className="w-5 h-5" />;
      default:
        return null;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'tool':
        return 'text-sky-600 bg-sky-100';
      case 'mcp':
        return 'text-sky-600 bg-sky-100';
      case 'agent':
        return 'text-sky-600 bg-sky-100';
      default:
        return 'text-slate-600 bg-slate-100';
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full md:w-4/5 lg:w-3/4 bg-white dark:bg-slate-900 shadow-2xl z-50 overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="brand-gradient text-white p-6 flex-shrink-0">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                    <SparklesIcon className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">Community Center</h2>
                    <p className="text-white/80 text-sm">Discover, Share & Collaborate</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* Stats Bar */}
              <div className="grid grid-cols-4 gap-4 bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">10K+</div>
                  <div className="text-xs text-white/70">Developers</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">∞</div>
                  <div className="text-xs text-white/70">Tools</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">500+</div>
                  <div className="text-xs text-white/70">MCPs</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">100+</div>
                  <div className="text-xs text-white/70">Agents</div>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 flex-shrink-0">
              <button
                onClick={() => setActiveTab('explore')}
                className={`flex-1 px-6 py-4 font-medium transition-colors ${
                  activeTab === 'explore'
                    ? 'text-sky-600 border-b-2 border-sky-600 bg-white dark:bg-slate-900'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                🔍 Explore Marketplace
              </button>
              <button
                onClick={() => setActiveTab('my-items')}
                className={`flex-1 px-6 py-4 font-medium transition-colors ${
                  activeTab === 'my-items'
                    ? 'text-sky-600 border-b-2 border-sky-600 bg-white dark:bg-slate-900'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                💼 My Items
              </button>
              <button
                onClick={() => setActiveTab('submit')}
                className={`flex-1 px-6 py-4 font-medium transition-colors ${
                  activeTab === 'submit'
                    ? 'text-sky-600 border-b-2 border-sky-600 bg-white dark:bg-slate-900'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                🚀 Submit
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {activeTab === 'explore' && (
                <div className="p-6 space-y-6">
                  {/* Search & Filters */}
                  <div className="space-y-4">
                    {/* Search Bar */}
                    <div className="relative">
                      <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                      <input
                        type="text"
                        placeholder="Search tools, MCPs, agents..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                      />
                    </div>

                    {/* Category Pills */}
                    <div className="flex flex-wrap gap-2">
                      {(['all', 'tool', 'mcp', 'agent'] as CategoryType[]).map((cat) => (
                        <button
                          key={cat}
                          onClick={() => setSelectedCategory(cat)}
                          className={`px-4 py-2 rounded-full font-medium transition-all ${
                            selectedCategory === cat
                              ? 'bg-sky-600 text-white shadow-lg'
                              : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                          }`}
                        >
                          {cat === 'all' ? '🌐 All' : cat === 'tool' ? '🛠️ Tools' : cat === 'mcp' ? '🔌 MCPs' : '🤖 Agents'}
                        </button>
                      ))}
                    </div>

                    {/* Sort Options */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-sm text-slate-600 dark:text-slate-400">
                        <FunnelIcon className="w-4 h-4" />
                        <span>Sort by:</span>
                      </div>
                      <div className="flex gap-2">
                        {(['trending', 'popular', 'recent', 'top-rated'] as SortType[]).map((sort) => (
                          <button
                            key={sort}
                            onClick={() => setSelectedSort(sort)}
                            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                              selectedSort === sort
                                ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                            }`}
                          >
                            {sort === 'trending' ? '🔥 Trending' : sort === 'popular' ? '⭐ Popular' : sort === 'recent' ? '🆕 Recent' : '🏆 Top Rated'}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Items Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {sortedItems.map((item) => (
                      <motion.div
                        key={item.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 hover:shadow-xl transition-shadow overflow-hidden group"
                      >
                        {/* Item Header */}
                        <div className="p-6 space-y-4">
                          {/* Top Row */}
                          <div className="flex items-start justify-between">
                            <div className="flex items-center space-x-3">
                              <div className={`p-2 rounded-xl ${getTypeColor(item.type)}`}>
                                {getTypeIcon(item.type)}
                              </div>
                              <div>
                                <div className="flex items-center space-x-2">
                                  <h3 className="font-bold text-lg text-slate-900 dark:text-white">{item.name}</h3>
                                  {item.verified && (
                                    <CheckBadgeIcon className="w-5 h-5 text-sky-500" title="Verified" />
                                  )}
                                  {item.premium && (
                                    <SparklesIcon className="w-5 h-5 text-yellow-500" title="Premium" />
                                  )}
                                </div>
                                <div className="flex items-center space-x-2 text-sm text-slate-500 dark:text-slate-400">
                                  <span>by {item.author.name}</span>
                                  {item.author.verified && (
                                    <CheckBadgeIcon className="w-4 h-4 text-sky-500" />
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Pricing Badge */}
                            {item.pricing.type === 'paid' ? (
                              <div className="flex items-center space-x-1 bg-gradient-to-r from-green-500 to-emerald-600 text-white px-3 py-1.5 rounded-full text-sm font-bold">
                                <CurrencyDollarIcon className="w-4 h-4" />
                                <span>${item.pricing.price}</span>
                              </div>
                            ) : (
                              <div className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-3 py-1.5 rounded-full text-sm font-bold">
                                FREE
                              </div>
                            )}
                          </div>

                          {/* Description */}
                          <p className="text-slate-600 dark:text-slate-300 text-sm line-clamp-2">
                            {item.description}
                          </p>

                          {/* Tags */}
                          <div className="flex flex-wrap gap-2">
                            {item.tags.slice(0, 4).map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs"
                              >
                                #{tag}
                              </span>
                            ))}
                          </div>

                          {/* Stats */}
                          <div className="grid grid-cols-4 gap-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                            <div className="text-center">
                              <div className="flex items-center justify-center space-x-1 text-yellow-500 mb-1">
                                <StarIconSolid className="w-4 h-4" />
                                <span className="font-bold text-sm text-slate-900 dark:text-white">
                                  {item.stats.rating.toFixed(1)}
                                </span>
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                {formatNumber(item.stats.reviews)} reviews
                              </div>
                            </div>
                            <div className="text-center">
                              <div className="flex items-center justify-center space-x-1 mb-1">
                                <ArrowDownTrayIcon className="w-4 h-4 text-sky-500" />
                                <span className="font-bold text-sm text-slate-900 dark:text-white">
                                  {formatNumber(item.stats.downloads)}
                                </span>
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">downloads</div>
                            </div>
                            <div className="text-center">
                              <div className="flex items-center justify-center space-x-1 mb-1">
                                <HeartIconSolid className="w-4 h-4 text-red-500" />
                                <span className="font-bold text-sm text-slate-900 dark:text-white">
                                  {formatNumber(item.stats.favorites)}
                                </span>
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">favorites</div>
                            </div>
                            <div className="text-center">
                              <div className="flex items-center justify-center space-x-1 mb-1">
                                <ChatBubbleLeftRightIcon className="w-4 h-4 text-sky-500" />
                                <span className="font-bold text-sm text-slate-900 dark:text-white">
                                  {formatNumber(item.stats.reviews)}
                                </span>
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">comments</div>
                            </div>
                          </div>

                          {/* Revenue Share Badge (for paid items) */}
                          {item.pricing.type === 'paid' && item.pricing.revenueShare && (
                            <div className="flex items-center justify-center space-x-2 bg-gradient-to-r from-slate-50 to-sky-50 dark:from-slate-900/35 dark:to-sky-900/25 border border-sky-200 dark:border-sky-800 rounded-xl p-3">
                              <TrophyIcon className="w-5 h-5 text-sky-600 dark:text-sky-400" />
                              <span className="text-sm font-medium text-sky-900 dark:text-sky-300">
                                Developer earns {item.pricing.revenueShare}% revenue share
                              </span>
                            </div>
                          )}

                          {/* Action Buttons */}
                          <div className="grid grid-cols-3 gap-2">
                            <button
                              onClick={() => {
                                setSelectedItem(item);
                                setShowComments(true);
                              }}
                              className="flex items-center justify-center space-x-2 px-4 py-2.5 brand-gradient hover:opacity-90 text-white rounded-xl font-medium transition-all transform hover:scale-105"
                            >
                              <ArrowDownTrayIcon className="w-4 h-4" />
                              <span>Install</span>
                            </button>
                            <button className="flex items-center justify-center space-x-2 px-4 py-2.5 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl font-medium transition-colors">
                              <HeartIcon className="w-4 h-4" />
                              <span>Save</span>
                            </button>
                            <button className="flex items-center justify-center space-x-2 px-4 py-2.5 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl font-medium transition-colors">
                              <ShareIcon className="w-4 h-4" />
                              <span>Share</span>
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {/* Empty State */}
                  {sortedItems.length === 0 && (
                    <div className="text-center py-16">
                      <div className="w-24 h-24 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                        <MagnifyingGlassIcon className="w-12 h-12 text-slate-400" />
                      </div>
                      <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">No items found</h3>
                      <p className="text-slate-600 dark:text-slate-400">Try adjusting your filters or search query</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'my-items' && (
                <div className="p-6">
                  <div className="text-center py-16">
                    <div className="w-24 h-24 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                      <CodeBracketIcon className="w-12 h-12 text-slate-400" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Your Submissions</h3>
                    <p className="text-slate-600 dark:text-slate-400 mb-6">
                      Tools, MCPs, and Agents you've shared with the community
                    </p>
                    <button className="px-6 py-3 brand-gradient hover:opacity-90 text-white rounded-xl font-medium transition-all">
                      Submit Your First Item
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'submit' && (
                <div className="p-6">
                  <div className="max-w-3xl mx-auto space-y-6">
                    <div className="bg-gradient-to-r from-slate-50 to-sky-50 dark:from-slate-900/35 dark:to-sky-900/25 border border-sky-200 dark:border-sky-800 rounded-2xl p-6">
                      <div className="flex items-start space-x-4">
                        <div className="w-12 h-12 brand-gradient rounded-xl flex items-center justify-center flex-shrink-0">
                          <TrophyIcon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
                            Earn Revenue from Your Creations
                          </h3>
                          <p className="text-slate-700 dark:text-slate-300 text-sm mb-4">
                            Submit verified, premium content and earn <strong>70% revenue share</strong> on all sales. 
                            Free items help build your reputation in the community.
                          </p>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex items-center space-x-2">
                              <CheckBadgeIcon className="w-5 h-5 text-green-500" />
                              <span className="text-slate-700 dark:text-slate-300">Verified badge for quality items</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <CurrencyDollarIcon className="w-5 h-5 text-green-500" />
                              <span className="text-slate-700 dark:text-slate-300">70/30 revenue split</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <UserGroupIcon className="w-5 h-5 text-green-500" />
                              <span className="text-slate-700 dark:text-slate-300">Reach 10K+ developers</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <SparklesIcon className="w-5 h-5 text-green-500" />
                              <span className="text-slate-700 dark:text-slate-300">Premium badge visibility</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Submit Form */}
                    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 space-y-6">
                      <h3 className="text-xl font-bold text-slate-900 dark:text-white">Submit New Item</h3>

                      {/* Type Selection */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                          Item Type
                        </label>
                        <div className="grid grid-cols-3 gap-4">
                          {[
                            { type: 'tool', icon: CodeBracketIcon, label: 'Tool', iconClass: 'text-sky-500 bg-sky-50 dark:bg-sky-900/30' },
                            { type: 'mcp', icon: ServerIcon, label: 'MCP Server', iconClass: 'text-sky-500 bg-sky-50 dark:bg-sky-900/30' },
                            { type: 'agent', icon: CpuChipIcon, label: 'Agent', iconClass: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/30' },
                          ].map((item) => (
                            <button
                              key={item.type}
                              className="flex flex-col items-center space-y-2 p-4 border-2 border-slate-200 dark:border-slate-600 rounded-xl hover:border-sky-500 hover:shadow-lg transition-all"
                            >
                              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.iconClass}`}>
                                <item.icon className="w-6 h-6" />
                              </div>
                              <span className="font-medium text-slate-900 dark:text-white">{item.label}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Form Fields */}
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Name
                          </label>
                          <input
                            type="text"
                            placeholder="e.g., Advanced Web Scraper"
                            className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Description
                          </label>
                          <textarea
                            rows={4}
                            placeholder="Describe what your tool/MCP/agent does..."
                            className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Tags (comma separated)
                          </label>
                          <input
                            type="text"
                            placeholder="e.g., scraping, automation, professional"
                            className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                          />
                        </div>

                        {/* Pricing */}
                        <div>
                          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                            Pricing Model
                          </label>
                          <div className="grid grid-cols-2 gap-4">
                            <button className="flex items-center justify-center space-x-2 p-4 border-2 border-slate-200 dark:border-slate-600 rounded-xl hover:border-green-500 transition-colors">
                              <span className="text-2xl">🎁</span>
                              <span className="font-medium">Free</span>
                            </button>
                            <button className="flex items-center justify-center space-x-2 p-4 border-2 border-sky-500 bg-sky-50 dark:bg-sky-900/20 rounded-xl">
                              <CurrencyDollarIcon className="w-5 h-5 text-sky-600" />
                              <span className="font-medium text-sky-600">Paid (70% revenue)</span>
                            </button>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Price (USD)
                          </label>
                          <input
                            type="number"
                            placeholder="29.99"
                            className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                          />
                        </div>

                        {/* File Upload */}
                        <div>
                          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Upload Files
                          </label>
                          <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl p-8 text-center hover:border-sky-500 transition-colors cursor-pointer">
                            <ArrowDownTrayIcon className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                            <p className="text-sm text-slate-600 dark:text-slate-400">
                              Drop files here or click to upload
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                              .py, .json, .yaml supported
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Submit Button */}
                      <button className="w-full py-4 brand-gradient hover:opacity-90 text-white rounded-xl font-bold text-lg transition-all transform hover:scale-105">
                        🚀 Submit for Review
                      </button>

                      <p className="text-xs text-center text-slate-500 dark:text-slate-400">
                        Items are reviewed within 24-48 hours. Verified items earn a quality badge.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>

          {/* Item Detail Modal */}
          <AnimatePresence>
            {showComments && selectedItem && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
                onClick={() => setShowComments(false)}
              >
                <motion.div
                  initial={{ scale: 0.9, y: 20 }}
                  animate={{ scale: 1, y: 0 }}
                  exit={{ scale: 0.9, y: 20 }}
                  onClick={(e) => e.stopPropagation()}
                  className="bg-white dark:bg-slate-800 rounded-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col"
                >
                  {/* Modal Header */}
                  <div className="p-6 border-b border-slate-200 dark:border-slate-700">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                          {selectedItem.name}
                        </h3>
                        <p className="text-slate-600 dark:text-slate-400">{selectedItem.description}</p>
                      </div>
                      <button
                        onClick={() => setShowComments(false)}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                      >
                        <XMarkIcon className="w-6 h-6 text-slate-500" />
                      </button>
                    </div>
                  </div>

                  {/* Comments Section */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    <h4 className="text-lg font-bold text-slate-900 dark:text-white">
                      Reviews & Comments ({selectedItem.stats.reviews})
                    </h4>

                    {mockComments[selectedItem.id]?.map((comment) => (
                      <div key={comment.id} className="space-y-4">
                        <div className="flex space-x-4">
                          <div className="w-10 h-10 brand-gradient rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                            {comment.author.avatar}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="font-bold text-slate-900 dark:text-white">
                                {comment.author.name}
                              </span>
                              <span className="text-sm text-slate-500 dark:text-slate-400">
                                @{comment.author.username}
                              </span>
                              <span className="text-sm text-slate-500 dark:text-slate-400">•</span>
                              <span className="text-sm text-slate-500 dark:text-slate-400">
                                {comment.createdAt}
                              </span>
                              {comment.rating > 0 && (
                                <>
                                  <span className="text-sm text-slate-500 dark:text-slate-400">•</span>
                                  <div className="flex items-center space-x-1">
                                    <StarIconSolid className="w-4 h-4 text-yellow-500" />
                                    <span className="text-sm font-bold text-slate-900 dark:text-white">
                                      {comment.rating}.0
                                    </span>
                                  </div>
                                </>
                              )}
                            </div>
                            <p className="text-slate-700 dark:text-slate-300">{comment.content}</p>

                            {/* Replies */}
                            {comment.replies.length > 0 && (
                              <div className="mt-4 ml-6 space-y-4 border-l-2 border-slate-200 dark:border-slate-700 pl-4">
                                {comment.replies.map((reply) => (
                                  <div key={reply.id} className="flex space-x-3">
                                    <div className="w-8 h-8 brand-gradient rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                                      {reply.author.avatar}
                                    </div>
                                    <div className="flex-1">
                                      <div className="flex items-center space-x-2 mb-1">
                                        <span className="font-bold text-sm text-slate-900 dark:text-white">
                                          {reply.author.name}
                                        </span>
                                        <span className="text-xs text-slate-500 dark:text-slate-400">
                                          {reply.createdAt}
                                        </span>
                                      </div>
                                      <p className="text-sm text-slate-700 dark:text-slate-300">{reply.content}</p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* Add Comment */}
                    <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
                      <textarea
                        rows={3}
                        placeholder="Add your review or comment..."
                        className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none"
                      />
                      <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-slate-600 dark:text-slate-400">Rating:</span>
                          {[1, 2, 3, 4, 5].map((star) => (
                            <StarIcon key={star} className="w-6 h-6 text-slate-400 hover:text-yellow-500 cursor-pointer transition-colors" />
                          ))}
                        </div>
                        <button className="px-6 py-2 brand-gradient hover:opacity-90 text-white rounded-lg font-medium transition-all">
                          Post Comment
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </AnimatePresence>
  );
};
