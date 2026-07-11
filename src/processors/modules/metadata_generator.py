"""
Metadata Generator Module - Generates YouTube metadata
"""

import re

class MetadataGenerator:
    """Generates YouTube title, description, and hashtags"""
    
    def generate_youtube_metadata(self, info):
        """Generate YouTube title, description, and hashtags from extracted information"""
        tournament = info.get('tournament_name', 'Chess Tournament')
        dates = info.get('dates', [])
        date_str = ', '.join(dates) if dates else ''
        venue = info.get('venue', '')
        categories = info.get('categories', [])
        entry_fee = info.get('entry_fee', '')
        prize_fund = info.get('prize_fund', '')
        contact = info.get('contact', [])
        email = info.get('email', [])
        website = info.get('website', [])
        
        # Generate TITLE
        title = self.generate_title(tournament, venue, date_str)
        
        # Generate DESCRIPTION
        description = self.generate_description(
            tournament, date_str, venue, categories, 
            entry_fee, prize_fund, contact, email, website
        )
        
        # Generate HASHTAGS
        hashtags = self.generate_hashtags(tournament, venue, categories)
        
        return title, description, hashtags
    
    def generate_title(self, tournament, venue, date_str):
        """Generate YouTube title"""
        title_parts = []
        title_parts.append(tournament)
        if venue and venue != "Online Classes Available":
            title_parts.append(venue)
        if date_str:
            title_parts.append(date_str)
        if "Chess" not in tournament and "chess" not in tournament:
            title_parts.append("Chess Tournament")
        
        title = " | ".join(title_parts)
        if len(title) > 100:
            if venue and venue != "Online Classes Available" and len(title) > 100:
                title_parts.remove(venue)
                title = " | ".join(title_parts)
            if len(title) > 100:
                title = title[:97] + "..."
        
        return title
    
    def generate_description(self, tournament, date_str, venue, categories, 
                           entry_fee, prize_fund, contact, email, website):
        """Generate YouTube description"""
        description_parts = []
        description_parts.append(f"🏆 {tournament.upper()}")
        description_parts.append("")
        
        if date_str:
            description_parts.append(f"📅 Dates: {date_str}")
        if venue and venue != "Online Classes Available":
            description_parts.append(f"📍 Venue: {venue}")
        if categories:
            description_parts.append(f"🏷️ Categories: {', '.join(categories)}")
        if entry_fee:
            description_parts.append(f"💰 Entry Fee: ₹{entry_fee}")
        if prize_fund:
            description_parts.append(f"🏆 Prize Fund: ₹{prize_fund}")
        if contact:
            description_parts.append(f"📞 Contact: {', '.join(contact)}")
        if email:
            description_parts.append(f"📧 Email: {', '.join(email)}")
        if website:
            description_parts.append(f"🌐 Website: {', '.join(website)}")
        
        description_parts.append("")
        description_parts.append("♟️ Join us for this exciting chess tournament!")
        description_parts.append("All chess enthusiasts are welcome to participate.")
        description_parts.append("")
        description_parts.append("🔹 Register Now!")
        description_parts.append("🔹 Limited Seats Available!")
        
        description = "\n".join(description_parts)
        if len(description) > 5000:
            description = description[:4997] + "..."
        
        return description
    
    def generate_hashtags(self, tournament, venue, categories):
        """Generate YouTube hashtags"""
        hashtag_parts = ["#Chess", "#ChessTournament"]
        
        if tournament and tournament != "Chess Tournament":
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', tournament.replace(' ', ''))
            if clean_name and len(clean_name) > 3:
                hashtag_parts.append(f"#{clean_name}")
        
        if venue and venue != "Online Classes Available":
            clean_venue = re.sub(r'[^a-zA-Z0-9]', '', venue.replace(' ', ''))
            if clean_venue and len(clean_venue) > 3:
                hashtag_parts.append(f"#{clean_venue}")
        
        for cat in categories[:3]:
            hashtag_parts.append(f"#{cat}")
        
        hashtag_parts.extend([
            "#ChessLife", "#ChessGame", "#ChessMasters",
            "#ChessGrandmaster", "#ChessLovers", "#ChessCommunity"
        ])
        
        hashtag_parts = list(dict.fromkeys(hashtag_parts))
        hashtags = " ".join(hashtag_parts)
        
        if len(hashtags) > 100:
            hashtag_parts = hashtag_parts[:5]
            hashtags = " ".join(hashtag_parts)
            if len(hashtags) > 100:
                hashtags = hashtags[:97] + "..."
        
        return hashtags