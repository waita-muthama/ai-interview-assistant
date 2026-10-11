from server.prompts import INSTRUCTIONS, build_prompt


def test_prompt_preserves_candidate_and_question():
    p = {'name': 'Alex', 'target_role': 'Network Engineer', 'experience': 'CCNA lab practice',
         'job_description': 'Maintain firewalls', 'resume_text': 'Worked with switches'}
    output = build_prompt('How do you configure a VLAN?', p, [], 'brief', 'technical')
    assert 'CCNA lab practice' in output
    assert 'How do you configure a VLAN?' in output
    assert 'Technically precise' in output
    assert 'Never invent' in INSTRUCTIONS
