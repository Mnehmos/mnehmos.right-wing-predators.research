#!/usr/bin/env python3
"""Update enrichments for batch 2 (IDs 903-919) with researched data"""

import json

# Updates to apply - keyed by ID
updates = {
    903: {
        "name": "Stephen Parshall",
        "year": 2020,
        "description": "Boogaloo Boys member arrested May 30, 2020, for conspiracy to damage buildings and government property using Molotov cocktails during George Floyd protests in Las Vegas. Also pleaded guilty to multiple counts of child sexual exploitation and child pornography on November 3, 2022. Sentenced to life with possibility of parole in 10 years for terrorism charges and 33 years for sexual exploitation crimes.",
        "crime": ["terrorism", "explosives", "child sexual exploitation", "child pornography"],
        "position": ["extremist/militia"],
        "tags": ["Boogaloo Boys", "domestic terrorism", "child abuse", "gun violence"]
    },
    904: {
        "name": "Jarl Judson Rockhill",
        "year": 2022,
        "description": "Jarl Judson Rockhill, 35, of West Linn, Oregon, convicted of sexual abuse in 2002 and 2003 and registered as sex offender. In 2010, convicted of felon in possession of a restricted weapon. In 2022, arrested for placing neo-Nazi propaganda on fence of Immigrant and Refugee Community Organization (IRCO) in Portland. Pled guilty to hate crime and sentenced to probation with anti-racist reading and writing requirements.",
        "crime": ["sexual abuse", "felon in possession of weapon", "hate crime"],
        "position": ["neo-Nazi", "extremist"],
        "tags": ["white supremacist", "hate crime", "sex offender", "extremist"]
    },
    905: {
        "name": "Jesse Shenk",
        "year": 2021,
        "description": "Jesse Shenk, member of the Goyim Defense League (GDL), a neo-Nazi antisemitic organization founded by Jon Minadeo II, was arrested in March 2021 and charged with child endangerment and sexual exploitation of a 14-year-old girl. He engaged with the minor online and planned to meet up with her. Shenk is identified as a convicted pedophile.",
        "crime": ["child endangerment", "sexual exploitation"],
        "position": ["white nationalist"],
        "tags": ["neo-Nazi", "antisemitic", "Goyim Defense League", "child abuse", "pedophile"]
    },
    906: {
        "name": "Kevin Alfred Strom",
        "year": 2008,
        "description": "Kevin Alfred Strom, founder of the white nationalist National Vanguard, was arrested January 4, 2007, in Greene County, Virginia, on charges of possession of child pornography and witness tampering. He pleaded guilty to one count of possession of child pornography in January 2008 and was sentenced to 23 months in prison, released September 3, 2008. In 1990, arrested for assaulting police officer during pro-apartheid rally.",
        "crime": ["child pornography", "witness tampering"],
        "position": ["white nationalist", "National Vanguard founder"],
        "tags": ["neo-Nazi", "child abuse", "white supremacist"]
    },
    908: {
        "name": "Robert Lee West",
        "year": None,
        "description": "Robert Lee West, Portland, Oregon, Patriot Prayer associate who has stalked and doxxed police and the DA. He was convicted of rape and mayhem in California.",
        "crime": ["rape", "mayhem"],
        "position": ["law enforcement", "extremist"],
        "tags": ["Patriot Prayer", "vigilantism", "doxxing"]
    },
    909: {
        "name": "Kyle Broussard",
        "year": None,
        "description": "Kyle Broussard, Patriot Prayer associated neo-Nazi, convicted of Rape 3.",
        "crime": ["rape"],
        "position": ["extremist"],
        "tags": ["Patriot Prayer", "white supremacist"]
    },
    910: {
        "name": "Jonathan Mark Myers",
        "year": 2022,
        "description": "Jonathan Mark Myers, 41, youth pastor and principal at Edinburgh parochial school, arrested October 27, 2022, on multiple felony charges including sexual misconduct with a minor and child seduction. Investigated for grooming and manipulating a victim starting at age 11-12, with inappropriate contact continuing into her adulthood. He threatened the victim with a firearm during one manipulative incident.",
        "crime": ["sexual misconduct with minor", "child seduction"],
        "position": ["youth pastor"],
        "tags": ["church abuse", "child abuse", "grooming", "gun violence"]
    },
    911: {
        "name": "Timothy Jason Jeltema",
        "year": 2022,
        "description": "Timothy Jason Jeltema, former student minister at Champion Forest Baptist Church in Houston, Texas, was arrested in June 2018 after a 13-year-old victim reported online sexual misconduct. Investigation revealed he communicated with and requested photographs from approximately 20-25 juveniles ages 14-17 via Instagram and Snapchat. Sentenced to five years in prison on November 17, 2022, after pleading guilty to online solicitation of a minor, indecency with a child, and sexual performance by a child.",
        "crime": ["online solicitation of minor", "indecency with child", "sexual performance by child"],
        "position": ["student minister", "Baptist"],
        "tags": ["church abuse", "child abuse", "online grooming"]
    },
    912: {
        "name": "Ryan Scott Walsh",
        "year": 2020,
        "description": "Ryan Scott Walsh, 27, youth director at Gulf Breeze Methodist Church, was arrested February 10, 2020, after reports of inappropriate contact with a 13-year-old female member of the youth group. Charged with transmitting obscene material to a minor, lewd and lascivious conduct involving a minor, and use of computer to solicit/seduce a child. Convicted and sentenced to more than 19 years in prison on October 7, 2020.",
        "crime": ["sexual offense with minor", "obscene material to minor", "online solicitation"],
        "position": ["youth director", "Methodist"],
        "tags": ["church abuse", "child abuse", "Methodist"]
    },
    914: {
        "name": "Michael Paul Keech",
        "year": 2022,
        "description": "Michael Paul Keech, 41, former youth pastor at West Columbia Baptist Church in Lexington, South Carolina, was arrested on October 20, 2022, and charged with four counts of criminal sexual conduct with a minor under 16. He allegedly sexually abused a teenage boy for more than two years, with incidents dating back to July 2019. Bond was denied and authorities sought to identify additional victims.",
        "crime": ["criminal sexual conduct with minor"],
        "position": ["youth pastor", "Southern Baptist"],
        "tags": ["church abuse", "child abuse", "Baptist", "sexual abuse"]
    },
    915: {
        "name": "Thomas James Brackett",
        "year": 2022,
        "description": "Thomas James Brackett, 59, former Baltimore County youth pastor and third grade teacher, was arrested in South Carolina on October 21, 2022, on 11 warrants for criminal sexual conduct with minors and child abuse. He allegedly sexually abused children ages 8-11 while serving as a teacher at Tabernacle Christian School and youth pastor in 1984-1985. At the time of arrest, he was pastor of Holy Trinity Pentecostal Church in Andrews, South Carolina.",
        "crime": ["criminal sexual conduct with minors", "child abuse", "sexual abuse"],
        "position": ["youth pastor", "teacher"],
        "tags": ["church abuse", "child abuse", "Pentecostal"]
    },
    916: {
        "name": "Sean Patrick Masopust",
        "year": 2022,
        "description": "Sean Patrick Masopust, 32, youth pastor at Northridge Church in Owatonna, Minnesota, was arrested February 2, 2022, for inappropriate relationship with a youth group member. During summer 2018, when Masopust was 28, he engaged in sexual contact with a 17-year-old, sending her nude photos and videos via Instagram and text, kissing her, and touching her inappropriately at the church and his home. Sentenced to 30 days confinement and 10 years probation.",
        "crime": ["criminal sexual conduct"],
        "position": ["youth pastor"],
        "tags": ["church abuse", "child abuse", "online grooming"]
    },
    917: {
        "name": "Michael D'Attoma",
        "year": 2022,
        "description": "Michael D'Attoma, former youth pastor at Northside Baptist Church in Lexington, South Carolina (2009-2012), was named in civil lawsuits filed in 2022 by two women alleging he sexually abused them beginning in 2010 when they were teens in his youth group. Allegations include grooming, inappropriate texting, Skype requests to remove clothing, and inappropriate touching. Criminal investigations are underway but he has not been criminally charged. D'Attoma denies the allegations.",
        "crime": ["sexual abuse allegations"],
        "position": ["youth pastor", "Southern Baptist"],
        "tags": ["church abuse", "child abuse", "civil litigation"]
    },
    918: {
        "name": "Sean M. Higgins",
        "year": 2020,
        "description": "Sean Higgins, 31, youth pastor and music leader at Harbor Baptist Church in Hainesport, New Jersey, and teacher at Harbor Baptist Academy, was arrested in October 2020. He victimized 13 boys ages 12-17 across seven states by pretending to be a teenage girl on Instagram and Snapchat, deceiving them into trading images, then blackmailing them to perform sexual acts. Indicted on 75 counts, he pled guilty to four counts of endangering the welfare of children and was sentenced to 27 years in prison.",
        "crime": ["online sexual exploitation of minors", "endangering welfare of child", "blackmail"],
        "position": ["youth pastor", "teacher", "Baptist"],
        "tags": ["church abuse", "child abuse", "online grooming", "Baptist"]
    },
    919: {
        "name": "Kenneth Leo Baker",
        "year": 2014,
        "description": "Kenneth Leo Baker, 44, of Ashland, Oregon, youth pastor at First Baptist Church of Ashland, faced four felony and two misdemeanor sex charges for alleged incidents involving a single victim between 2006 and 2011. At least four incidents occurred when the girl was younger than 14. Arrested in October 2014 after confessing to church leaders, he pleaded guilty and received a sentence of 10.5 years in prison.",
        "crime": ["sexual contact with juvenile"],
        "position": ["youth pastor"],
        "tags": ["church abuse", "child abuse", "Baptist"]
    }
}

# Load enrichments
with open('/home/user/right-wing-predators/manual_enrichments.json', 'r', encoding='utf-8') as f:
    enrichments = json.load(f)

# Update matching entries
updated_count = 0
for entry in enrichments:
    if entry['id'] in updates:
        update_data = updates[entry['id']]
        for key, value in update_data.items():
            entry[key] = value
        updated_count += 1

# Save updated enrichments
with open('/home/user/right-wing-predators/manual_enrichments.json', 'w', encoding='utf-8') as f:
    json.dump(enrichments, f, indent=2, ensure_ascii=False)

print(f"Updated {updated_count} enrichments in batch 2")
