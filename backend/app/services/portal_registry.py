"""
State Portal Registry: Maps Indian states/UTs to their grievance portals,
official complaint email addresses, and helpline numbers.

Provides smart routing logic to select the best submission channel
based on the user's state and complaint type.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class ComplaintCategory(str, Enum):
    MISCONDUCT = "misconduct"
    OVERCHARGE = "overcharge"
    GENERAL = "general"


class SubmissionMethod(str, Enum):
    EMAIL = "email"
    WEB_PORTAL = "web_portal"
    BOTH = "both"


@dataclass
class PortalInfo:
    name: str
    url: str
    portal_type: str  # igrs, traffic, police, rto, central
    supports_automation: bool = False
    complaint_form_url: Optional[str] = None
    status_check_url: Optional[str] = None


@dataclass
class StatePortalConfig:
    state_name: str
    state_code: str
    portals: Dict[str, PortalInfo] = field(default_factory=dict)
    emails: Dict[str, List[str]] = field(default_factory=dict)
    helplines: Dict[str, str] = field(default_factory=dict)
    default_portal: str = "pgportal"
    preferred_method: SubmissionMethod = SubmissionMethod.EMAIL


CENTRAL_PORTAL = PortalInfo(
    name="CPGRAMS / PG Portal",
    url="https://pgportal.gov.in/",
    portal_type="central",
    supports_automation=True,
    complaint_form_url="https://pgportal.gov.in/Registration",
    status_check_url="https://pgportal.gov.in/GrievanceStatus",
)

CENTRAL_EMAILS = {
    "misconduct": [
        "pgportal-mpp@gov.in",
    ],
    "overcharge": [
        "grievance-morth@gov.in",
        "pgportal-mpp@gov.in",
    ],
    "general": [
        "pgportal-mpp@gov.in",
    ],
}

CENTRAL_HELPLINES = {
    "pgportal": "1800-11-0031",
    "traffic_national": "112",
    "highway": "1033",
    "consumer": "1800-11-4000",
}

# ---------------------------------------------------------------------------
# Full state/UT registry
# ---------------------------------------------------------------------------

STATE_REGISTRY: Dict[str, StatePortalConfig] = {

    # ---- States ----

    "andhra_pradesh": StatePortalConfig(
        state_name="Andhra Pradesh",
        state_code="AP",
        portals={
            "igrs": PortalInfo(
                name="Meekosam (AP Grievance Portal)",
                url="https://meekosam.ap.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="AP Police",
                url="https://www.appolice.gov.in/",
                portal_type="police",
            ),
            "transport": PortalInfo(
                name="AP Transport Department",
                url="https://transport.ap.gov.in/",
                portal_type="rto",
            ),
        },
        emails={
            "misconduct": [
                "dgp-ap@ap.gov.in",
                "spgrievance-hyd@appolice.gov.in",
            ],
            "overcharge": [
                "commissioner-transport@ap.gov.in",
            ],
            "general": [
                "meekosam@ap.gov.in",
                "dgp-ap@ap.gov.in",
            ],
        },
        helplines={"police": "100", "traffic": "0866-2573666", "women": "181"},
        default_portal="igrs",
    ),

    "arunachal_pradesh": StatePortalConfig(
        state_name="Arunachal Pradesh",
        state_code="AR",
        portals={
            "police": PortalInfo(
                name="Arunachal Pradesh Police",
                url="https://arunpol.nic.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-arn@nic.in"],
            "overcharge": ["transport-arn@nic.in"],
            "general": ["dgp-arn@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "assam": StatePortalConfig(
        state_name="Assam",
        state_code="AS",
        portals={
            "igrs": PortalInfo(
                name="Assam Jan Sunwai",
                url="https://jansunwai.assam.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Assam Police",
                url="https://police.assam.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgp@assampolice.gov.in",
                "grievance@assampolice.gov.in",
            ],
            "overcharge": ["commissioner-transport@assam.gov.in"],
            "general": ["dgp@assampolice.gov.in"],
        },
        helplines={"police": "100", "traffic": "0361-2540138"},
        default_portal="igrs",
    ),

    "bihar": StatePortalConfig(
        state_name="Bihar",
        state_code="BR",
        portals={
            "igrs": PortalInfo(
                name="Bihar Grievance Portal",
                url="https://grievance.bihar.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Bihar Police",
                url="https://biharpolice.bih.nic.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgp-bih@nic.in",
                "grievance-bihar@gov.in",
            ],
            "overcharge": ["transport-bih@nic.in"],
            "general": ["grievance-bihar@gov.in"],
        },
        helplines={"police": "100", "traffic": "0612-2233580", "highway": "1033"},
        default_portal="igrs",
    ),

    "chhattisgarh": StatePortalConfig(
        state_name="Chhattisgarh",
        state_code="CG",
        portals={
            "igrs": PortalInfo(
                name="Jan Shikayat CG",
                url="https://janshikayat.cg.nic.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Chhattisgarh Police",
                url="https://cgpolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp@cgpolice.gov.in"],
            "overcharge": ["transport.commissioner@cg.gov.in"],
            "general": ["janshikayat@cg.nic.in"],
        },
        helplines={"police": "100", "traffic": "0771-2511192"},
        default_portal="igrs",
    ),

    "goa": StatePortalConfig(
        state_name="Goa",
        state_code="GA",
        portals={
            "police": PortalInfo(
                name="Goa Police",
                url="https://www.goapolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp@goapolice.gov.in"],
            "overcharge": ["dto-goa@nic.in"],
            "general": ["dgp@goapolice.gov.in"],
        },
        helplines={"police": "100", "traffic": "0832-2425454"},
        default_portal="pgportal",
    ),

    "gujarat": StatePortalConfig(
        state_name="Gujarat",
        state_code="GJ",
        portals={
            "igrs": PortalInfo(
                name="Gujarat CM Helpline / Swagat Online",
                url="https://swagat.gujarat.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Gujarat Police",
                url="https://police.gujarat.gov.in/",
                portal_type="police",
            ),
            "traffic": PortalInfo(
                name="Gujarat Traffic Police",
                url="https://traffic.gujarat.gov.in/",
                portal_type="traffic",
            ),
        },
        emails={
            "misconduct": [
                "dgpgujarat@gujarat.gov.in",
                "grievance-gj@gov.in",
            ],
            "overcharge": ["commissioner-transport@gujarat.gov.in"],
            "general": ["swagat@gujarat.gov.in"],
        },
        helplines={"police": "100", "traffic": "079-27500555", "women": "181"},
        default_portal="igrs",
    ),

    "haryana": StatePortalConfig(
        state_name="Haryana",
        state_code="HR",
        portals={
            "igrs": PortalInfo(
                name="Har Samadhan",
                url="https://harsamadhan.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Haryana Police",
                url="https://haryanapolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgpharyana@hry.nic.in",
                "adgp-law@hry.nic.in",
            ],
            "overcharge": ["transport-commissioner@hry.nic.in"],
            "general": ["harsamadhan@hry.nic.in"],
        },
        helplines={"police": "100", "traffic": "0172-2749900", "women": "1091"},
        default_portal="igrs",
    ),

    "himachal_pradesh": StatePortalConfig(
        state_name="Himachal Pradesh",
        state_code="HP",
        portals={
            "igrs": PortalInfo(
                name="HP CM Helpline",
                url="https://cmhelpline.hp.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Himachal Pradesh Police",
                url="https://hppolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-hp@nic.in"],
            "overcharge": ["transport-hp@nic.in"],
            "general": ["cmhelpline-hp@nic.in"],
        },
        helplines={"police": "100", "cm_helpline": "1100"},
        default_portal="igrs",
    ),

    "jharkhand": StatePortalConfig(
        state_name="Jharkhand",
        state_code="JH",
        portals={
            "igrs": PortalInfo(
                name="Jan Sunwai Jharkhand",
                url="https://jansunwai.jharkhand.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Jharkhand Police",
                url="https://jhpolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp@jhpolice.gov.in"],
            "overcharge": ["transport-jh@nic.in"],
            "general": ["jansunwai@jharkhand.gov.in"],
        },
        helplines={"police": "100", "traffic": "0651-2490855"},
        default_portal="igrs",
    ),

    "karnataka": StatePortalConfig(
        state_name="Karnataka",
        state_code="KA",
        portals={
            "igrs": PortalInfo(
                name="Karnataka PGRS",
                url="https://pgrs.karnataka.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Karnataka State Police",
                url="https://www.ksp.gov.in/",
                portal_type="police",
            ),
            "traffic": PortalInfo(
                name="Bangalore Traffic Police",
                url="https://btp.gov.in/",
                portal_type="traffic",
            ),
        },
        emails={
            "misconduct": [
                "dgpoffice@ksp.gov.in",
                "complaint@ksp.gov.in",
            ],
            "overcharge": [
                "commissioner-transport@karnataka.gov.in",
            ],
            "general": [
                "pgrs@karnataka.gov.in",
                "dgpoffice@ksp.gov.in",
            ],
        },
        helplines={"police": "100", "traffic": "080-22942222", "btp": "080-22943024"},
        default_portal="igrs",
    ),

    "kerala": StatePortalConfig(
        state_name="Kerala",
        state_code="KL",
        portals={
            "igrs": PortalInfo(
                name="Kerala CM Grievance Cell",
                url="https://cmo.kerala.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Kerala Police",
                url="https://keralapolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgp@keralapolice.gov.in",
                "complaint@keralapolice.gov.in",
            ],
            "overcharge": ["transport-commissioner@kerala.gov.in"],
            "general": [
                "cmo@kerala.gov.in",
                "dgp@keralapolice.gov.in",
            ],
        },
        helplines={"police": "100", "traffic": "0471-2722500", "women": "1515"},
        default_portal="igrs",
    ),

    "madhya_pradesh": StatePortalConfig(
        state_name="Madhya Pradesh",
        state_code="MP",
        portals={
            "igrs": PortalInfo(
                name="Samadhan MP",
                url="https://samadhan.mp.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="MP Police",
                url="https://mppolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgp@mppolice.gov.in",
                "phq-grievance@mppolice.gov.in",
            ],
            "overcharge": ["transport-mp@nic.in"],
            "general": [
                "samadhan@mp.gov.in",
                "dgp@mppolice.gov.in",
            ],
        },
        helplines={"police": "100", "traffic": "0755-2443737", "women": "1091"},
        default_portal="igrs",
    ),

    "maharashtra": StatePortalConfig(
        state_name="Maharashtra",
        state_code="MH",
        portals={
            "igrs": PortalInfo(
                name="IGRS Maharashtra",
                url="https://igrs.maharashtra.gov.in/",
                portal_type="igrs",
                supports_automation=True,
                complaint_form_url="https://igrs.maharashtra.gov.in/Home/Registration",
            ),
            "police": PortalInfo(
                name="Maharashtra Police",
                url="https://citizen.mahapolice.gov.in/",
                portal_type="police",
            ),
            "traffic": PortalInfo(
                name="Maharashtra Traffic Police",
                url="https://www.mahatrafficpolice.gov.in/",
                portal_type="traffic",
            ),
            "transport": PortalInfo(
                name="Maharashtra RTO / Parivahan",
                url="https://transport.maharashtra.gov.in/",
                portal_type="rto",
            ),
        },
        emails={
            "misconduct": [
                "dgpcontrol@mahapolice.gov.in",
                "igrs@maharashtra.gov.in",
            ],
            "overcharge": [
                "transport.commissioner@maharashtra.gov.in",
                "igrs@maharashtra.gov.in",
            ],
            "general": [
                "igrs@maharashtra.gov.in",
                "dgpcontrol@mahapolice.gov.in",
            ],
        },
        helplines={
            "police": "100",
            "traffic": "022-24937747",
            "highway": "1033",
            "women": "103",
        },
        default_portal="igrs",
    ),

    "manipur": StatePortalConfig(
        state_name="Manipur",
        state_code="MN",
        portals={
            "police": PortalInfo(
                name="Manipur Police",
                url="https://manipurpolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-manipur@nic.in"],
            "overcharge": ["transport-mn@nic.in"],
            "general": ["dgp-manipur@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "meghalaya": StatePortalConfig(
        state_name="Meghalaya",
        state_code="ML",
        portals={
            "police": PortalInfo(
                name="Meghalaya Police",
                url="https://megpolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-meg@nic.in"],
            "overcharge": ["transport-meg@nic.in"],
            "general": ["dgp-meg@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "mizoram": StatePortalConfig(
        state_name="Mizoram",
        state_code="MZ",
        portals={
            "police": PortalInfo(
                name="Mizoram Police",
                url="https://police.mizoram.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-mz@nic.in"],
            "overcharge": ["transport-mz@nic.in"],
            "general": ["dgp-mz@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "nagaland": StatePortalConfig(
        state_name="Nagaland",
        state_code="NL",
        portals={
            "police": PortalInfo(
                name="Nagaland Police",
                url="https://nagapol.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgpnagaland@nagapol.gov.in"],
            "overcharge": ["transport-nl@nic.in"],
            "general": ["dgpnagaland@nagapol.gov.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "odisha": StatePortalConfig(
        state_name="Odisha",
        state_code="OD",
        portals={
            "igrs": PortalInfo(
                name="Odisha Grievance Portal",
                url="https://grievance.odisha.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Odisha Police",
                url="https://odishapolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgp@odishapolice.gov.in",
                "grievance@odisha.gov.in",
            ],
            "overcharge": ["transport-odisha@nic.in"],
            "general": ["grievance@odisha.gov.in"],
        },
        helplines={"police": "100", "traffic": "0674-2405611"},
        default_portal="igrs",
    ),

    "punjab": StatePortalConfig(
        state_name="Punjab",
        state_code="PB",
        portals={
            "igrs": PortalInfo(
                name="Connect Punjab",
                url="https://connect.punjab.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Punjab Police",
                url="https://punjabpolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgppunjab@punjabpolice.gov.in",
                "grievance@punjab.gov.in",
            ],
            "overcharge": ["sta-punjab@nic.in"],
            "general": ["connect@punjab.gov.in"],
        },
        helplines={"police": "100", "traffic": "0172-2740479", "women": "1091"},
        default_portal="igrs",
    ),

    "rajasthan": StatePortalConfig(
        state_name="Rajasthan",
        state_code="RJ",
        portals={
            "igrs": PortalInfo(
                name="Rajasthan Sampark",
                url="https://sampark.rajasthan.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Rajasthan Police",
                url="https://police.rajasthan.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgp@rajpolice.gov.in",
                "sampark@rajasthan.gov.in",
            ],
            "overcharge": ["transport-rj@nic.in"],
            "general": ["sampark@rajasthan.gov.in"],
        },
        helplines={"police": "100", "traffic": "0141-2744418", "women": "1091"},
        default_portal="igrs",
    ),

    "sikkim": StatePortalConfig(
        state_name="Sikkim",
        state_code="SK",
        portals={
            "police": PortalInfo(
                name="Sikkim Police",
                url="https://sikkimpolice.nic.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-sikkim@nic.in"],
            "overcharge": ["transport-sk@nic.in"],
            "general": ["dgp-sikkim@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "tamil_nadu": StatePortalConfig(
        state_name="Tamil Nadu",
        state_code="TN",
        portals={
            "igrs": PortalInfo(
                name="TN CM Cell",
                url="https://cmdashboard.tn.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Tamil Nadu Police",
                url="https://eservices.tnpolice.gov.in/",
                portal_type="police",
            ),
            "traffic": PortalInfo(
                name="Chennai Traffic Police",
                url="https://chennaitrafficpolice.tn.gov.in/",
                portal_type="traffic",
            ),
        },
        emails={
            "misconduct": [
                "dgp@tnpolice.gov.in",
                "grievance@tn.gov.in",
            ],
            "overcharge": ["transport-tn@nic.in"],
            "general": [
                "grievance@tn.gov.in",
                "dgp@tnpolice.gov.in",
            ],
        },
        helplines={"police": "100", "traffic": "103", "women": "1091"},
        default_portal="igrs",
    ),

    "telangana": StatePortalConfig(
        state_name="Telangana",
        state_code="TS",
        portals={
            "igrs": PortalInfo(
                name="Telangana Grievance Portal",
                url="https://grievances.telangana.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Telangana Police",
                url="https://www.tspolice.gov.in/",
                portal_type="police",
            ),
            "traffic": PortalInfo(
                name="Hyderabad Traffic Police",
                url="https://htp.gov.in/",
                portal_type="traffic",
            ),
        },
        emails={
            "misconduct": [
                "dgp@tspolice.gov.in",
                "grievances@telangana.gov.in",
            ],
            "overcharge": ["transport-ts@telangana.gov.in"],
            "general": [
                "grievances@telangana.gov.in",
                "dgp@tspolice.gov.in",
            ],
        },
        helplines={"police": "100", "traffic": "040-27852482", "women": "181"},
        default_portal="igrs",
    ),

    "tripura": StatePortalConfig(
        state_name="Tripura",
        state_code="TR",
        portals={
            "police": PortalInfo(
                name="Tripura Police",
                url="https://tripurapolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-tripura@nic.in"],
            "overcharge": ["transport-tr@nic.in"],
            "general": ["dgp-tripura@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "uttar_pradesh": StatePortalConfig(
        state_name="Uttar Pradesh",
        state_code="UP",
        portals={
            "igrs": PortalInfo(
                name="IGRS UP / Jansunwai",
                url="https://jansunwai.up.nic.in/",
                portal_type="igrs",
                supports_automation=True,
                complaint_form_url="https://jansunwai.up.nic.in/Registration.aspx",
            ),
            "police": PortalInfo(
                name="UP Police",
                url="https://uppolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgpup@up.nic.in",
                "jansunwai-up@gov.in",
            ],
            "overcharge": [
                "transport-up@nic.in",
                "jansunwai-up@gov.in",
            ],
            "general": [
                "jansunwai-up@gov.in",
                "dgpup@up.nic.in",
            ],
        },
        helplines={"police": "100", "traffic": "0522-2638844", "women": "1090"},
        default_portal="igrs",
    ),

    "uttarakhand": StatePortalConfig(
        state_name="Uttarakhand",
        state_code="UK",
        portals={
            "igrs": PortalInfo(
                name="Uttarakhand CM Helpline",
                url="https://cmhelpline.uk.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Uttarakhand Police",
                url="https://uttarakhandpolice.uk.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-uk@nic.in"],
            "overcharge": ["transport-uk@nic.in"],
            "general": ["cmhelpline-uk@nic.in"],
        },
        helplines={"police": "100", "cm_helpline": "1905"},
        default_portal="igrs",
    ),

    "west_bengal": StatePortalConfig(
        state_name="West Bengal",
        state_code="WB",
        portals={
            "igrs": PortalInfo(
                name="WB CM Grievance Cell",
                url="https://wbcmo.gov.in/grievance.aspx",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="West Bengal Police",
                url="https://wbpolice.gov.in/",
                portal_type="police",
            ),
            "traffic": PortalInfo(
                name="Kolkata Traffic Police",
                url="https://kolkatatrafficpolice.gov.in/",
                portal_type="traffic",
            ),
        },
        emails={
            "misconduct": [
                "dgpwestbengal@gmail.com",
                "grievance-wbcmo@gov.in",
            ],
            "overcharge": ["transport-wb@nic.in"],
            "general": ["grievance-wbcmo@gov.in"],
        },
        helplines={"police": "100", "traffic": "033-22143024", "women": "1091"},
        default_portal="igrs",
    ),

    # ---- Union Territories ----

    "delhi": StatePortalConfig(
        state_name="Delhi",
        state_code="DL",
        portals={
            "igrs": PortalInfo(
                name="Delhi PGMS",
                url="https://pgms.delhi.gov.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="Delhi Police",
                url="https://delhipolice.gov.in/",
                portal_type="police",
            ),
            "traffic": PortalInfo(
                name="Delhi Traffic Police",
                url="https://delhitrafficpolice.nic.in/",
                portal_type="traffic",
            ),
        },
        emails={
            "misconduct": [
                "cp.delhi@delhipolice.gov.in",
                "jcp.traffic@delhipolice.gov.in",
                "pgms-delhi@gov.in",
            ],
            "overcharge": [
                "transport-dl@nic.in",
                "jcp.traffic@delhipolice.gov.in",
            ],
            "general": [
                "pgms-delhi@gov.in",
                "cp.delhi@delhipolice.gov.in",
            ],
        },
        helplines={
            "police": "100",
            "traffic": "011-25844444",
            "women": "1091",
            "highway": "1033",
        },
        default_portal="igrs",
    ),

    "chandigarh": StatePortalConfig(
        state_name="Chandigarh",
        state_code="CH",
        portals={
            "police": PortalInfo(
                name="Chandigarh Police",
                url="https://chandigarhpolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["ssp-chd@nic.in"],
            "overcharge": ["rla-chd@nic.in"],
            "general": ["ssp-chd@nic.in"],
        },
        helplines={"police": "100", "traffic": "0172-2749900"},
        default_portal="pgportal",
    ),

    "puducherry": StatePortalConfig(
        state_name="Puducherry",
        state_code="PY",
        portals={
            "police": PortalInfo(
                name="Puducherry Police",
                url="https://police.py.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp.pon@nic.in"],
            "overcharge": ["transport-py@nic.in"],
            "general": ["dgp.pon@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "jammu_kashmir": StatePortalConfig(
        state_name="Jammu & Kashmir",
        state_code="JK",
        portals={
            "igrs": PortalInfo(
                name="J&K Grievance Portal",
                url="https://jkgrievance.nic.in/",
                portal_type="igrs",
            ),
            "police": PortalInfo(
                name="J&K Police",
                url="https://jkpolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": [
                "dgp-jk@jkpolice.gov.in",
                "grievance-jk@nic.in",
            ],
            "overcharge": ["transport-jk@nic.in"],
            "general": ["grievance-jk@nic.in"],
        },
        helplines={"police": "100", "traffic": "0194-2452786"},
        default_portal="igrs",
    ),

    "ladakh": StatePortalConfig(
        state_name="Ladakh",
        state_code="LA",
        portals={
            "police": PortalInfo(
                name="Ladakh Police",
                url="https://ladakhpolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["igp-ladakh@nic.in"],
            "overcharge": ["transport-la@nic.in"],
            "general": ["igp-ladakh@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "andaman_nicobar": StatePortalConfig(
        state_name="Andaman & Nicobar Islands",
        state_code="AN",
        portals={
            "police": PortalInfo(
                name="A&N Police",
                url="https://police.andaman.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["dgp-and@nic.in"],
            "overcharge": ["transport-and@nic.in"],
            "general": ["dgp-and@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "dadra_nagar_haveli_daman_diu": StatePortalConfig(
        state_name="Dadra & Nagar Haveli and Daman & Diu",
        state_code="DD",
        portals={
            "police": PortalInfo(
                name="DNH & DD Police",
                url="https://dyvsp-silvassa.nic.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["sp-silvassa@nic.in"],
            "overcharge": ["rto-daman@nic.in"],
            "general": ["sp-silvassa@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),

    "lakshadweep": StatePortalConfig(
        state_name="Lakshadweep",
        state_code="LD",
        portals={
            "police": PortalInfo(
                name="Lakshadweep Police",
                url="https://lakshadweeppolice.gov.in/",
                portal_type="police",
            ),
        },
        emails={
            "misconduct": ["sp-lk@nic.in"],
            "overcharge": ["transport-lk@nic.in"],
            "general": ["sp-lk@nic.in"],
        },
        helplines={"police": "100"},
        default_portal="pgportal",
    ),
}


# ---------------------------------------------------------------------------
# Aliases: normalise various user-input formats to registry keys
# ---------------------------------------------------------------------------

_STATE_ALIASES: Dict[str, str] = {
    # Full names (lowercase)
    "andhra pradesh": "andhra_pradesh",
    "arunachal pradesh": "arunachal_pradesh",
    "himachal pradesh": "himachal_pradesh",
    "madhya pradesh": "madhya_pradesh",
    "tamil nadu": "tamil_nadu",
    "uttar pradesh": "uttar_pradesh",
    "west bengal": "west_bengal",
    "jammu kashmir": "jammu_kashmir",
    "jammu & kashmir": "jammu_kashmir",
    "jammu and kashmir": "jammu_kashmir",
    "andaman nicobar": "andaman_nicobar",
    "andaman & nicobar": "andaman_nicobar",
    "andaman and nicobar": "andaman_nicobar",
    "andaman and nicobar islands": "andaman_nicobar",
    "dadra nagar haveli": "dadra_nagar_haveli_daman_diu",
    "dadra & nagar haveli": "dadra_nagar_haveli_daman_diu",
    "dadra nagar haveli and daman diu": "dadra_nagar_haveli_daman_diu",
    "dadra & nagar haveli and daman & diu": "dadra_nagar_haveli_daman_diu",
    "daman diu": "dadra_nagar_haveli_daman_diu",
    "daman & diu": "dadra_nagar_haveli_daman_diu",
    # State codes
    "ap": "andhra_pradesh",
    "ar": "arunachal_pradesh",
    "as": "assam",
    "br": "bihar",
    "cg": "chhattisgarh",
    "ga": "goa",
    "gj": "gujarat",
    "hr": "haryana",
    "hp": "himachal_pradesh",
    "jh": "jharkhand",
    "ka": "karnataka",
    "kl": "kerala",
    "mp": "madhya_pradesh",
    "mh": "maharashtra",
    "mn": "manipur",
    "ml": "meghalaya",
    "mz": "mizoram",
    "nl": "nagaland",
    "od": "odisha",
    "pb": "punjab",
    "rj": "rajasthan",
    "sk": "sikkim",
    "tn": "tamil_nadu",
    "ts": "telangana",
    "tr": "tripura",
    "up": "uttar_pradesh",
    "uk": "uttarakhand",
    "wb": "west_bengal",
    "dl": "delhi",
    "ch": "chandigarh",
    "py": "puducherry",
    "jk": "jammu_kashmir",
    "la": "ladakh",
    "an": "andaman_nicobar",
    "dd": "dadra_nagar_haveli_daman_diu",
    "ld": "lakshadweep",
    # Common short forms
    "j&k": "jammu_kashmir",
    "a&n": "andaman_nicobar",
}


def _normalise_state(raw: str) -> str:
    """Convert any state input to a registry key."""
    key = raw.strip().lower().replace("-", "_").replace("  ", " ")
    if key in STATE_REGISTRY:
        return key
    if key in _STATE_ALIASES:
        return _STATE_ALIASES[key]
    # Try without underscores/spaces
    compact = key.replace("_", "").replace(" ", "")
    for alias, registry_key in _STATE_ALIASES.items():
        if alias.replace(" ", "").replace("_", "") == compact:
            return registry_key
    return key


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class SubmissionTarget:
    """The resolved submission plan for a complaint."""
    state_name: str
    state_code: str
    portal: PortalInfo
    emails: List[str]
    cc_emails: List[str]
    helplines: Dict[str, str]
    preferred_method: SubmissionMethod
    all_portals: Dict[str, PortalInfo]


def get_state_config(state: str) -> Optional[StatePortalConfig]:
    """Look up state config, returning None for unknown states."""
    key = _normalise_state(state)
    return STATE_REGISTRY.get(key)


def resolve_submission_target(
    state: str,
    complaint_type: str = "general",
) -> SubmissionTarget:
    """
    Given a user's state and complaint type, return the best submission target
    including portal, email addresses, and helplines.

    Falls back to Central PG Portal for unknown states.
    """
    key = _normalise_state(state)
    config = STATE_REGISTRY.get(key)

    category = complaint_type.lower()
    if category not in ("misconduct", "overcharge", "general"):
        category = "general"

    if config is None:
        logger.warning(f"Unknown state '{state}', falling back to central portal")
        return SubmissionTarget(
            state_name=state.title(),
            state_code="XX",
            portal=CENTRAL_PORTAL,
            emails=CENTRAL_EMAILS.get(category, CENTRAL_EMAILS["general"]),
            cc_emails=[],
            helplines=CENTRAL_HELPLINES,
            preferred_method=SubmissionMethod.EMAIL,
            all_portals={"pgportal": CENTRAL_PORTAL},
        )

    # Pick the best portal for this complaint type
    portal = _select_best_portal(config, category)

    # Primary emails for this complaint type
    primary_emails = config.emails.get(category, [])
    if not primary_emails:
        primary_emails = config.emails.get("general", [])

    # CC the central PG Portal email for escalation visibility
    cc_emails = CENTRAL_EMAILS.get(category, CENTRAL_EMAILS["general"])

    # Merge helplines: state + central
    helplines = {**CENTRAL_HELPLINES, **config.helplines}

    return SubmissionTarget(
        state_name=config.state_name,
        state_code=config.state_code,
        portal=portal,
        emails=primary_emails,
        cc_emails=cc_emails,
        helplines=helplines,
        preferred_method=config.preferred_method,
        all_portals=config.portals,
    )


def _select_best_portal(
    config: StatePortalConfig,
    category: str,
) -> PortalInfo:
    """
    Pick the most relevant portal for the complaint category.

    Priority:
      misconduct -> police portal -> igrs -> central
      overcharge -> traffic/rto portal -> igrs -> central
      general    -> igrs -> police -> central
    """
    portals = config.portals

    preference_map = {
        "misconduct": ["police", "igrs", "traffic"],
        "overcharge": ["traffic", "transport", "rto", "igrs"],
        "general": ["igrs", "police", "traffic"],
    }

    for preferred_type in preference_map.get(category, ["igrs"]):
        for portal in portals.values():
            if portal.portal_type == preferred_type:
                return portal

    # Fallback: default portal from config, or first available, or central
    if config.default_portal in portals:
        return portals[config.default_portal]
    if portals:
        return next(iter(portals.values()))
    return CENTRAL_PORTAL


def get_all_states() -> List[Dict[str, str]]:
    """Return a list of all supported states for frontend dropdowns."""
    return [
        {
            "key": key,
            "name": cfg.state_name,
            "code": cfg.state_code,
            "default_portal": cfg.default_portal,
        }
        for key, cfg in sorted(STATE_REGISTRY.items(), key=lambda x: x[1].state_name)
    ]


def get_supported_portals_for_state(state: str) -> Dict[str, Dict[str, Any]]:
    """Return all portal options for a given state (for frontend portal selector)."""
    key = _normalise_state(state)
    config = STATE_REGISTRY.get(key)

    result: Dict[str, Dict[str, Any]] = {
        "pgportal": {
            "name": CENTRAL_PORTAL.name,
            "url": CENTRAL_PORTAL.url,
            "type": CENTRAL_PORTAL.portal_type,
        },
    }

    if config:
        for portal_key, portal in config.portals.items():
            result[portal_key] = {
                "name": portal.name,
                "url": portal.url,
                "type": portal.portal_type,
            }

    return result


def get_helplines_for_state(state: str) -> Dict[str, str]:
    """Return combined helpline numbers (state + central)."""
    key = _normalise_state(state)
    config = STATE_REGISTRY.get(key)
    helplines = dict(CENTRAL_HELPLINES)
    if config:
        helplines.update(config.helplines)
    return helplines
