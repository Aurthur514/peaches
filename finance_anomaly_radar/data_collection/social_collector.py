"""
Social Media Collector for Finance Anomaly Radar
Collects and analyzes social media data for identifying fake influencers and suspicious investment groups.
"""

import re
import json
import networkx as nx
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import asyncio
import aiohttp
from textblob import TextBlob
from loguru import logger

from .base_collector import BaseDataCollector

class SocialMediaCollector(BaseDataCollector):
    """Collects social media data for network analysis and bot detection."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.social_graph = nx.DiGraph()
        self.user_profiles = {}
        self.group_data = {}
        self.bot_patterns = self._load_bot_patterns()
        
    def _load_bot_patterns(self) -> Dict[str, Any]:
        """Load patterns that indicate bot behavior."""
        return {
            'username_patterns': [
                r'^[a-zA-Z]+\d{4,}$',  # Name followed by 4+ digits
                r'^[a-zA-Z]+_[a-zA-Z]+\d+$',  # FirstName_LastName + digits
                r'^user\d+$',  # Generic user patterns
                r'^.*crypto.*trader.*$',  # Crypto trader names
                r'^.*investment.*expert.*$'  # Investment expert names
            ],
            'activity_patterns': {
                'min_posts_per_day': 20,  # Unusually high posting frequency
                'max_human_posts_per_hour': 10,
                'copy_paste_threshold': 0.8,  # 80% similar content
                'engagement_anomaly_ratio': 10  # Likes/followers ratio anomaly
            },
            'content_patterns': {
                'promotional_keywords': [
                    'guaranteed profit', 'risk-free', 'exclusive signal',
                    'join group', 'limited spots', 'hurry up',
                    'dm for details', 'link in bio', 'click link',
                    'investment opportunity', 'crypto signals'
                ],
                'spam_indicators': [
                    'repeated_hashtags', 'excessive_emojis', 
                    'multiple_links', 'all_caps_text'
                ]
            },
            'network_patterns': {
                'suspicious_follower_growth': 1000,  # Followers gained per day
                'bot_follower_ratio': 0.3,  # 30% bot followers
                'circular_following_size': 5  # Circular following networks
            }
        }
    
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect social media data from various platforms.
        
        Returns:
            List of social media data points
        """
        collected_data = []
        
        # Collect Twitter/X data
        twitter_data = await self._collect_twitter_data()
        collected_data.extend(twitter_data)
        
        # Collect Telegram group data
        telegram_data = await self._collect_telegram_groups()
        collected_data.extend(telegram_data)
        
        # Collect YouTube channel data
        youtube_data = await self._collect_youtube_data()
        collected_data.extend(youtube_data)
        
        # Analyze collected data for network patterns
        network_analysis = self._analyze_social_networks(collected_data)
        collected_data.extend(network_analysis)
        
        return collected_data
    
    async def _collect_twitter_data(self) -> List[Dict[str, Any]]:
        """Collect Twitter data for financial influencers and groups."""
        twitter_data = []
        
        try:
            # Sample Twitter data (in production, use Twitter API v2)
            sample_profiles = [
                {
                    'platform': 'twitter',
                    'user_id': 'crypto_guru_2024',
                    'username': 'CryptoGuru2024',
                    'display_name': 'Crypto Investment Expert',
                    'followers': 50000,
                    'following': 100,
                    'posts_count': 5000,
                    'account_created': '2024-01-01',
                    'verification_status': False,
                    'bio': 'Crypto signals 🚀 | 500% profits guaranteed | DM for VIP group',
                    'profile_image': 'crypto_avatar.jpg',
                    'recent_posts': [
                        {
                            'post_id': 'post_001',
                            'text': '🚀 URGENT: New crypto signal! 1000% guaranteed! Limited spots in our VIP group. DM now!',
                            'timestamp': datetime.utcnow().isoformat(),
                            'likes': 500,
                            'retweets': 200,
                            'replies': 50,
                            'hashtags': ['#crypto', '#trading', '#signals'],
                            'mentions': ['@crypto_exchange']
                        }
                    ],
                    'network_connections': [
                        {'connected_user': 'trader_bot_123', 'relationship': 'mutual_follow'},
                        {'connected_user': 'investment_scam_456', 'relationship': 'mutual_follow'}
                    ]
                }
            ]
            
            for profile in sample_profiles:
                # Add bot detection analysis
                profile['bot_analysis'] = self._analyze_bot_probability(profile)
                profile['influence_score'] = self._calculate_influence_score(profile)
                profile['scam_indicators'] = self._extract_scam_indicators_social(profile)
                
                twitter_data.append(profile)
        
        except Exception as e:
            logger.error(f"Error collecting Twitter data: {e}")
        
        return twitter_data
    
    async def _collect_telegram_groups(self) -> List[Dict[str, Any]]:
        """Collect Telegram group data for investment scams."""
        telegram_data = []
        
        try:
            # Sample Telegram group data
            sample_groups = [
                {
                    'platform': 'telegram',
                    'group_id': 'investment_signals_vip',
                    'group_name': 'VIP Investment Signals 💰',
                    'group_type': 'private',
                    'members_count': 5000,
                    'created_date': '2024-01-15',
                    'description': 'Exclusive investment signals with 90% accuracy. Join now for guaranteed profits!',
                    'admin_count': 5,
                    'recent_messages': [
                        {
                            'message_id': 'msg_001',
                            'sender': 'admin_crypto_expert',
                            'text': 'New signal: Buy ABC coin now! Target 500% profit in 24 hours!',
                            'timestamp': datetime.utcnow().isoformat(),
                            'reactions': {'thumbs_up': 100, 'fire': 50}
                        }
                    ],
                    'member_activity': {
                        'messages_per_day': 200,
                        'new_members_per_day': 100,
                        'leaving_members_per_day': 20
                    }
                }
            ]
            
            for group in sample_groups:
                # Analyze group for scam patterns
                group['scam_analysis'] = self._analyze_group_scam_patterns(group)
                group['member_analysis'] = self._analyze_group_members(group)
                
                telegram_data.append(group)
        
        except Exception as e:
            logger.error(f"Error collecting Telegram data: {e}")
        
        return telegram_data
    
    async def _collect_youtube_data(self) -> List[Dict[str, Any]]:
        """Collect YouTube channel data for financial advice scams."""
        youtube_data = []
        
        try:
            # Sample YouTube channel data
            sample_channels = [
                {
                    'platform': 'youtube',
                    'channel_id': 'get_rich_quick_2024',
                    'channel_name': 'Get Rich Quick Methods',
                    'subscribers': 100000,
                    'videos_count': 500,
                    'channel_created': '2023-12-01',
                    'description': 'Learn secret methods to make money online. Cryptocurrency trading signals and investment tips.',
                    'recent_videos': [
                        {
                            'video_id': 'vid_001',
                            'title': 'I Made $10,000 in 1 Hour with This Secret Method!',
                            'views': 50000,
                            'likes': 2000,
                            'dislikes': 100,
                            'upload_date': datetime.utcnow().isoformat(),
                            'duration': 600,  # 10 minutes
                            'description': 'Click link in description to join exclusive group!'
                        }
                    ]
                }
            ]
            
            for channel in sample_channels:
                # Analyze channel for scam patterns
                channel['scam_analysis'] = self._analyze_youtube_scam_patterns(channel)
                
                youtube_data.append(channel)
        
        except Exception as e:
            logger.error(f"Error collecting YouTube data: {e}")
        
        return youtube_data
    
    def _analyze_bot_probability(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze probability that a social media profile is a bot.
        
        Args:
            profile: Social media profile data
            
        Returns:
            Bot analysis results
        """
        analysis = {
            'bot_probability': 0.0,
            'bot_indicators': [],
            'human_indicators': [],
            'confidence': 0.0
        }
        
        try:
            username = profile.get('username', '')
            patterns = self.bot_patterns['username_patterns']
            
            # Check username patterns
            username_score = 0
            for pattern in patterns:
                if re.match(pattern, username, re.IGNORECASE):
                    username_score += 0.2
                    analysis['bot_indicators'].append(f'username_pattern_{pattern[:10]}...')
            
            # Check follower/following ratio
            followers = profile.get('followers', 0)
            following = profile.get('following', 0)
            
            if followers > 0 and following > 0:
                ratio = followers / following
                if ratio > 100:  # Suspiciously high follower ratio
                    username_score += 0.15
                    analysis['bot_indicators'].append('high_follower_ratio')
                elif ratio < 0.1:  # Suspiciously low follower ratio
                    username_score += 0.1
                    analysis['bot_indicators'].append('low_follower_ratio')
            
            # Check posting frequency
            posts_count = profile.get('posts_count', 0)
            account_created = profile.get('account_created')
            
            if account_created:
                try:
                    created_date = datetime.fromisoformat(account_created)
                    account_age_days = (datetime.utcnow() - created_date).days
                    
                    if account_age_days > 0:
                        posts_per_day = posts_count / account_age_days
                        
                        if posts_per_day > self.bot_patterns['activity_patterns']['min_posts_per_day']:
                            username_score += 0.2
                            analysis['bot_indicators'].append('high_posting_frequency')
                except Exception:
                    pass
            
            # Check bio content for promotional keywords
            bio = profile.get('bio', '').lower()
            promotional_keywords = self.bot_patterns['content_patterns']['promotional_keywords']
            
            keyword_matches = sum([1 for keyword in promotional_keywords if keyword in bio])
            if keyword_matches > 2:
                username_score += 0.15
                analysis['bot_indicators'].append('promotional_bio')
            
            # Check recent posts for spam patterns
            recent_posts = profile.get('recent_posts', [])
            if recent_posts:
                spam_score = self._analyze_spam_content(recent_posts)
                username_score += spam_score * 0.2
                
                if spam_score > 0.5:
                    analysis['bot_indicators'].append('spam_content')
            
            # Human indicators
            if profile.get('verification_status'):
                username_score -= 0.3
                analysis['human_indicators'].append('verified_account')
            
            if len(recent_posts) > 0:
                # Check for genuine engagement patterns
                avg_engagement = sum([
                    post.get('likes', 0) + post.get('retweets', 0) + post.get('replies', 0)
                    for post in recent_posts
                ]) / len(recent_posts)
                
                if followers > 0:
                    engagement_rate = avg_engagement / followers
                    if 0.01 <= engagement_rate <= 0.1:  # Healthy engagement rate
                        username_score -= 0.1
                        analysis['human_indicators'].append('healthy_engagement')
            
            analysis['bot_probability'] = max(0.0, min(1.0, username_score))
            analysis['confidence'] = 0.8 if len(analysis['bot_indicators']) + len(analysis['human_indicators']) >= 3 else 0.5
        
        except Exception as e:
            logger.warning(f"Error in bot analysis: {e}")
        
        return analysis
    
    def _analyze_spam_content(self, posts: List[Dict[str, Any]]) -> float:
        """Analyze posts for spam content patterns."""
        if not posts:
            return 0.0
        
        spam_score = 0.0
        
        # Check for repeated content
        post_texts = [post.get('text', '') for post in posts]
        unique_texts = set(post_texts)
        
        if len(post_texts) > 0:
            uniqueness_ratio = len(unique_texts) / len(post_texts)
            if uniqueness_ratio < 0.5:  # Less than 50% unique content
                spam_score += 0.3
        
        # Check for excessive hashtags and links
        for post in posts:
            text = post.get('text', '')
            hashtag_count = len(re.findall(r'#\w+', text))
            link_count = len(re.findall(r'http[s]?://\S+', text))
            emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text))
            
            if hashtag_count > 5:
                spam_score += 0.1
            if link_count > 2:
                spam_score += 0.1
            if emoji_count > 10:
                spam_score += 0.1
            
            # Check for all caps
            if len(text) > 10 and text.isupper():
                spam_score += 0.1
        
        return min(spam_score / len(posts), 1.0)
    
    def _calculate_influence_score(self, profile: Dict[str, Any]) -> float:
        """Calculate influence score for a social media profile."""
        try:
            followers = profile.get('followers', 0)
            posts_count = profile.get('posts_count', 0)
            
            # Base score from follower count (logarithmic scale)
            if followers > 0:
                follower_score = min(np.log10(followers) / 7, 1.0)  # Max at 10M followers
            else:
                follower_score = 0
            
            # Engagement score from recent posts
            engagement_score = 0
            recent_posts = profile.get('recent_posts', [])
            
            if recent_posts and followers > 0:
                total_engagement = sum([
                    post.get('likes', 0) + post.get('retweets', 0) + post.get('replies', 0)
                    for post in recent_posts
                ])
                
                avg_engagement = total_engagement / len(recent_posts)
                engagement_rate = avg_engagement / followers
                engagement_score = min(engagement_rate * 50, 1.0)  # Normalize to 0-1
            
            # Verification bonus
            verification_bonus = 0.2 if profile.get('verification_status') else 0
            
            # Account age factor
            age_factor = 1.0
            account_created = profile.get('account_created')
            if account_created:
                try:
                    created_date = datetime.fromisoformat(account_created)
                    account_age_days = (datetime.utcnow() - created_date).days
                    age_factor = min(account_age_days / 365, 1.0)  # Max after 1 year
                except Exception:
                    pass
            
            influence_score = (follower_score * 0.4 + engagement_score * 0.4 + verification_bonus) * age_factor
            return min(influence_score, 1.0)
        
        except Exception as e:
            logger.warning(f"Error calculating influence score: {e}")
            return 0.0
    
    def _extract_scam_indicators_social(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract scam indicators from social media profile."""
        indicators = {
            'promotional_content': False,
            'guaranteed_returns': False,
            'group_invitations': False,
            'financial_advice': False,
            'urgency_language': False,
            'contact_outside_platform': False,
            'risk_score': 0.0
        }
        
        try:
            # Analyze bio
            bio = profile.get('bio', '').lower()
            
            promotional_keywords = self.bot_patterns['content_patterns']['promotional_keywords']
            for keyword in promotional_keywords:
                if keyword in bio:
                    if 'guaranteed' in keyword:
                        indicators['guaranteed_returns'] = True
                    elif 'group' in keyword:
                        indicators['group_invitations'] = True
                    elif 'dm' in keyword or 'link' in keyword:
                        indicators['contact_outside_platform'] = True
                    
                    indicators['promotional_content'] = True
            
            # Analyze recent posts
            recent_posts = profile.get('recent_posts', [])
            for post in recent_posts:
                text = post.get('text', '').lower()
                
                if any(word in text for word in ['investment', 'trading', 'profit', 'money']):
                    indicators['financial_advice'] = True
                
                if any(word in text for word in ['urgent', 'limited', 'now', 'hurry']):
                    indicators['urgency_language'] = True
                
                if any(word in text for word in ['guaranteed', 'risk-free', '100%']):
                    indicators['guaranteed_returns'] = True
            
            # Calculate risk score
            risk_factors = sum([1 for indicator in indicators.values() if isinstance(indicator, bool) and indicator])
            indicators['risk_score'] = min(risk_factors / 5, 1.0)
        
        except Exception as e:
            logger.warning(f"Error extracting scam indicators: {e}")
        
        return indicators
    
    def _analyze_group_scam_patterns(self, group: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Telegram group for scam patterns."""
        analysis = {
            'scam_probability': 0.0,
            'scam_indicators': [],
            'member_growth_anomaly': False,
            'content_analysis': {}
        }
        
        try:
            # Check group name and description
            group_name = group.get('group_name', '').lower()
            description = group.get('description', '').lower()
            
            scam_keywords = ['vip', 'exclusive', 'guaranteed', 'signals', 'profit', 'investment']
            keyword_matches = sum([1 for keyword in scam_keywords if keyword in group_name + ' ' + description])
            
            if keyword_matches > 2:
                analysis['scam_indicators'].append('promotional_keywords')
            
            # Check member growth patterns
            member_activity = group.get('member_activity', {})
            new_members_per_day = member_activity.get('new_members_per_day', 0)
            leaving_members_per_day = member_activity.get('leaving_members_per_day', 0)
            
            if new_members_per_day > 50:  # Rapid growth
                analysis['member_growth_anomaly'] = True
                analysis['scam_indicators'].append('rapid_member_growth')
            
            if leaving_members_per_day > new_members_per_day * 0.5:  # High churn
                analysis['scam_indicators'].append('high_member_churn')
            
            # Analyze recent messages
            recent_messages = group.get('recent_messages', [])
            if recent_messages:
                financial_messages = 0
                promotional_messages = 0
                
                for message in recent_messages:
                    text = message.get('text', '').lower()
                    
                    if any(word in text for word in ['buy', 'sell', 'profit', 'target', 'signal']):
                        financial_messages += 1
                    
                    if any(word in text for word in ['join', 'group', 'vip', 'exclusive']):
                        promotional_messages += 1
                
                total_messages = len(recent_messages)
                if total_messages > 0:
                    financial_ratio = financial_messages / total_messages
                    promotional_ratio = promotional_messages / total_messages
                    
                    analysis['content_analysis'] = {
                        'financial_content_ratio': financial_ratio,
                        'promotional_content_ratio': promotional_ratio
                    }
                    
                    if financial_ratio > 0.7:
                        analysis['scam_indicators'].append('high_financial_content')
                    
                    if promotional_ratio > 0.3:
                        analysis['scam_indicators'].append('high_promotional_content')
            
            # Calculate overall scam probability
            indicator_count = len(analysis['scam_indicators'])
            analysis['scam_probability'] = min(indicator_count * 0.2, 1.0)
        
        except Exception as e:
            logger.warning(f"Error analyzing group scam patterns: {e}")
        
        return analysis
    
    def _analyze_group_members(self, group: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze group members for suspicious patterns."""
        return {
            'estimated_bot_ratio': 0.3,  # Placeholder
            'new_account_ratio': 0.4,
            'engagement_patterns': 'suspicious'
        }
    
    def _analyze_youtube_scam_patterns(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze YouTube channel for scam patterns."""
        analysis = {
            'scam_probability': 0.0,
            'scam_indicators': [],
            'content_patterns': {}
        }
        
        try:
            # Check channel name and description
            channel_name = channel.get('channel_name', '').lower()
            description = channel.get('description', '').lower()
            
            scam_phrases = ['get rich quick', 'secret method', 'make money fast', 'guaranteed income']
            for phrase in scam_phrases:
                if phrase in channel_name + ' ' + description:
                    analysis['scam_indicators'].append(f'scam_phrase_{phrase.replace(" ", "_")}')
            
            # Analyze recent videos
            recent_videos = channel.get('recent_videos', [])
            if recent_videos:
                clickbait_count = 0
                money_focused_count = 0
                
                for video in recent_videos:
                    title = video.get('title', '').lower()
                    
                    # Check for clickbait patterns
                    if any(word in title for word in ['secret', 'shocking', 'you won\'t believe']):
                        clickbait_count += 1
                    
                    # Check for money-focused content
                    if any(word in title for word in ['$', 'money', 'profit', 'rich', 'income']):
                        money_focused_count += 1
                
                total_videos = len(recent_videos)
                if total_videos > 0:
                    clickbait_ratio = clickbait_count / total_videos
                    money_ratio = money_focused_count / total_videos
                    
                    analysis['content_patterns'] = {
                        'clickbait_ratio': clickbait_ratio,
                        'money_focused_ratio': money_ratio
                    }
                    
                    if clickbait_ratio > 0.5:
                        analysis['scam_indicators'].append('high_clickbait_content')
                    
                    if money_ratio > 0.7:
                        analysis['scam_indicators'].append('money_focused_content')
            
            # Calculate scam probability
            indicator_count = len(analysis['scam_indicators'])
            analysis['scam_probability'] = min(indicator_count * 0.25, 1.0)
        
        except Exception as e:
            logger.warning(f"Error analyzing YouTube scam patterns: {e}")
        
        return analysis
    
    def _analyze_social_networks(self, collected_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze social network connections for suspicious patterns."""
        network_analysis = []
        
        try:
            # Build social graph from collected data
            for item in collected_data:
                if item.get('platform') in ['twitter', 'telegram']:
                    user_id = item.get('user_id') or item.get('group_id')
                    
                    if user_id:
                        # Add node to graph
                        self.social_graph.add_node(user_id, **item)
                        
                        # Add connections
                        connections = item.get('network_connections', [])
                        for conn in connections:
                            connected_user = conn.get('connected_user')
                            if connected_user:
                                self.social_graph.add_edge(user_id, connected_user)
            
            # Analyze network patterns
            if len(self.social_graph.nodes()) > 0:
                network_metrics = {
                    'data_type': 'network_analysis',
                    'timestamp': datetime.utcnow().isoformat(),
                    'total_nodes': len(self.social_graph.nodes()),
                    'total_edges': len(self.social_graph.edges()),
                    'network_density': nx.density(self.social_graph),
                    'connected_components': nx.number_weakly_connected_components(self.social_graph),
                    'suspicious_clusters': self._detect_suspicious_clusters()
                }
                
                network_analysis.append(network_metrics)
        
        except Exception as e:
            logger.warning(f"Error in network analysis: {e}")
        
        return network_analysis
    
    def _detect_suspicious_clusters(self) -> List[Dict[str, Any]]:
        """Detect suspicious clusters in the social network."""
        clusters = []
        
        try:
            # Find strongly connected components
            components = list(nx.weakly_connected_components(self.social_graph))
            
            for component in components:
                if len(component) > 5:  # Clusters with more than 5 users
                    subgraph = self.social_graph.subgraph(component)
                    
                    # Analyze cluster properties
                    bot_count = 0
                    high_risk_count = 0
                    
                    for node in component:
                        node_data = self.social_graph.nodes[node]
                        bot_analysis = node_data.get('bot_analysis', {})
                        scam_indicators = node_data.get('scam_indicators', {})
                        
                        if bot_analysis.get('bot_probability', 0) > 0.7:
                            bot_count += 1
                        
                        if scam_indicators.get('risk_score', 0) > 0.6:
                            high_risk_count += 1
                    
                    cluster_info = {
                        'cluster_size': len(component),
                        'bot_ratio': bot_count / len(component),
                        'high_risk_ratio': high_risk_count / len(component),
                        'network_density': nx.density(subgraph),
                        'is_suspicious': (bot_count / len(component)) > 0.5 or (high_risk_count / len(component)) > 0.3
                    }
                    
                    clusters.append(cluster_info)
        
        except Exception as e:
            logger.warning(f"Error detecting suspicious clusters: {e}")
        
        return clusters
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate social media data.
        
        Args:
            data: Social media data to validate
            
        Returns:
            True if data is valid
        """
        required_fields = ['platform']
        
        for field in required_fields:
            if field not in data:
                return False
        
        # Platform-specific validation
        platform = data['platform']
        
        if platform == 'twitter':
            return 'user_id' in data and 'username' in data
        elif platform == 'telegram':
            return 'group_id' in data and 'group_name' in data
        elif platform == 'youtube':
            return 'channel_id' in data and 'channel_name' in data
        
        return True
    
    def get_collection_interval(self) -> int:
        """Get social media collection interval."""
        return self.config.get('collection_interval', 300)  # Every 5 minutes