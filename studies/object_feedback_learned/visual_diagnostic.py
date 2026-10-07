"""Private overlays for diagnosed failures, using original chronological replay."""
import gzip,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'vendor/co-tracker'))
sys.path.append(str(ROOT/'studies/object_feedback_feasibility'))
from fyp.runtime import make_env,sensor_images
from camera_reference import CameraReferenceCapture
from private_reference import reference,truth

rows=[json.loads(line) for line in gzip.open(HERE/'endpoint_samples.jsonl.gz','rt')]
visible=[r for r in rows if r['reference_visible'] is True and r['accepted']]
occluded=[r for r in rows if r['reference_visible'] is False and r['accepted']]
cases=[dict(label='background_depth',row=max(visible,key=lambda r:r['world_error_m'])),
       dict(label='wrist_frame_drift',row=max([r for r in visible if r['camera']=='robot0_eye_in_hand' and r['reference_body']=='frame_root'],key=lambda r:r['world_error_m'])),
       dict(label='occluded_accepted',row=max(occluded,key=lambda r:r['world_error_m']))]
cohort=json.loads((ROOT/'studies/object_feedback_feasibility/cohort.json').read_text())
checks=[]
for episode in sorted({c['row']['episode'] for c in cases}):
    relevant=[c for c in cases if c['row']['episode']==episode]
    run=ROOT/'runs'/episode;config=json.loads((run/'config.json').read_text());saved=np.load(run/'trajectory.npz')
    env,obs,initial=make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
    assert np.array_equal(initial,saved['initial'])
    segments=[s for s in cohort['streams'] if s['episode']==episode]
    capture=CameraReferenceCapture(env,segments,reference,truth)
    for index,action in enumerate(saved['actions'][:max(c['row']['step'] for c in relevant)]):
        step=index+1;capture.step=step;obs,_,_,_=env.step(action)
        assert np.array_equal(env.get_sim_state(),saved['states'][index])
        for case in [c for c in relevant if c['row']['step']==step]:
            r=case['row'];camera=r['camera'];rgb,depth=sensor_images(env,obs)[camera]
            ref=capture.seeds[(r['query_decision'],r['pixel_index'])]
            sampled=capture.measurements[camera];expected,visible_now=truth(env.sim,ref,depth,sampled['calibration'])
            assert visible_now==r['reference_visible']
            camera_matrix=np.asarray(sampled['calibration']['camera_to_world'])
            optical=(np.linalg.inv(camera_matrix)@np.r_[expected,1])[:3]
            projected=np.asarray(sampled['calibration']['intrinsic'])@optical
            actual_pixel=projected[:2]/projected[2]
            assert abs(np.linalg.norm(np.asarray(r['world_xyz'])-expected)-r['world_error_m'])<1e-12
            frame=Image.new('RGB',(640,620),'white')
            frame.paste(Image.fromarray(rgb).resize((512,512)),(64,0));draw=ImageDraw.Draw(frame)
            x,y=np.asarray(r['pixel'])*2+[64,0];draw.ellipse((x-7,y-7,x+7,y+7),outline='#ff8a00',width=3)
            u,v=actual_pixel*2+[64,0];draw.line((u-7,v-7,u+7,v+7),fill='#00f080',width=3);draw.line((u-7,v+7,u+7,v-7),fill='#00f080',width=3)
            text=f"{case['label']} | {episode}\n{camera}, query {r['query_decision']} point {r['pixel_index']}, step {step}\nOrange: tracker pixel. Green: PRIVATE reference projection.\nAccepted error {r['world_error_m']*1000:.2f} mm; reference visible: {visible_now}"
            draw.multiline_text((12,520),text,fill='black',spacing=6)
            frame.save(HERE/(case['label']+'.png'))
            x,y=map(lambda z:int(round(z)),r['pixel'])
            checks.append(dict(label=case['label'],row=r,private_reference_pixel=actual_pixel.tolist(),
                tracked_pixel_metric_depth=float(depth[y,x]),private_reference_optical_depth_m=float(optical[2]),
                reference_error_reproduced_exactly=True,chronological_action_states_exact=True,camera_age_seconds=float(env.sim.data.time-sampled['time'])))
            print(case['label'],'reproduced',flush=True)
    env.close()
(HERE/'visual_diagnostic.json').write_text(json.dumps(dict(scope='Post-result private diagnosis; no estimator or cohort change.',cases=checks),indent=2)+'\n')
