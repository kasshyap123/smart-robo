"""Rev I: service hood and removable universal power/interface carrier.
Purchased boards remain envelope budgets, not supplied printed components.
"""
from pathlib import Path
import sys,json,shutil,importlib.util,hashlib
BASE=Path(__file__).resolve().parents[1]
SOURCE=BASE/'outputs/rover_revH_SUPPORT_REVIEW_2026-10-11'
DEST=BASE/'outputs/rover_revI_CAD_2026-10-12'
sys.path.insert(0,str(SOURCE/'cad'))
spec=importlib.util.spec_from_file_location('build_util',SOURCE/'cad/build_util.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
from design import rr,box,cyl,hexprism,cut,fuse

def old(pid):return dict(op='import',path=f'input_step/{pid}.step')
def shell():
    rib=box(8.6,80,6,107,-40,29)
    holes=[cyl(3.4,12,110,y,28) for y in [-33,33]]
    nuts=[hexprism(5.8,2.8,110,y,29) for y in [-33,33]]
    return cut(fuse(old('B01'),rib),*holes,*nuts)
def electronics_tray():
    # Female housings and lead bends pass through the original floor.
    base=cut(old('B05'),*[rr(7,40,17,2,x=x,y=25,z=39) for x in [-91,-65]])
    arms=[box(19,10,6,-6,y-5,29) for y in [-33,33]]
    posts=[box(5,10,18,-6,y-5,29) for y in [-33,33]]
    return cut(fuse(base,*arms,*posts),
        *[cyl(3.4,12,8,y,28) for y in [-33,33]],
        *[hexprism(5.8,2.8,8,y,29) for y in [-33,33]])
def lid():
    # Open a 51.2 x 52 mm well, with a 2.5 mm perimeter wall and roof.
    # Existing perimeter lid fasteners and USB notch are retained.
    hood=cut(rr(56.2,57,10.5,3,x=-28.9,y=26.5,z=78),
             rr(51.2,52,9,1,x=-28.9,y=26.5,z=77),
             *[rr(4,34,5,1.5,x=x,y=26.5,z=85) for x in [-47,-38,-29,-20,-11]])
    return fuse(cut(old('B04'),rr(51.2,52,10,1,x=-28.9,y=26.5,z=74)),hood)
def tray():
    slots=[rr(12,3.4,5,1.6,x=x,y=y,z=34) for x in [30,50,70,90] for y in [-30,-10,10,30]
           if (x,y)!=(90,-10)]
    return cut(fuse(rr(92,78,3,3,x=60,y=0,z=35),*[rr(18,11,3,3,x=x,y=y,z=35) for x in [12,106] for y in [-33,33]]),
        *[cyl(3.4,5,x,y,34) for x in [8,110] for y in [-33,33]],
        rr(24,14,5,2,x=87,y=-3,z=34),*slots)
CHANGES={'B01':shell,'B04':lid,'B05':electronics_tray,'B14':tray}
def main():
    assert not DEST.exists(),'Revision already exists; never overwrite a delivered revision.'
    for folder in ['cad','input_step','master_step','positioned_step','PRINT_ALL','verification']:(DEST/folder).mkdir(parents=True)
    for folder in ['master_step','positioned_step','PRINT_ALL']:
        for p in (SOURCE/folder).iterdir():
            if p.is_file():shutil.copy2(p,DEST/folder/p.name)
    for p in (SOURCE/'verification').glob('*_print.stl'):shutil.copy2(p,DEST/'verification'/p.name)
    for p in (SOURCE/'master_step').glob('*.step'):shutil.copy2(p,DEST/'input_step'/p.name)
    for name in ['design.py','mesh_utils.py','build_util.py']:shutil.copy2(SOURCE/'cad'/name,DEST/'cad'/name)
    shutil.copy2(Path(__file__),DEST/'cad/build_revI.py')
    records=json.loads((SOURCE/'parts.json').read_text())
    records.append(dict(id='B14',name='Removable universal power and interface tray',quantity=1))
    # New part has no prior master; hash the explicit design recipe as provenance.
    shutil.copy2(Path(__file__),DEST/'input_step/B14.design.py')
    g.ROOT=DEST;g.CHANGED=set(CHANGES);g.shape=lambda pid:CHANGES[pid]()
    # Export the new source recipe as a genuine STEP solid for provenance.
    writer=g.Writer(); solid=writer.emit(tray())
    writer.lines += [f'Save "{DEST}/input_step/B14.step";', 'Printf("COMPLETE");']
    g.run('B14_recipe_source',writer.lines)
    updated=[]
    for r in records:
        updated.append(g.build(r) if r['id'] in CHANGES else dict(r,geometry_changed=False))
    (DEST/'parts.json').write_text(json.dumps(updated,indent=2)+'\n')
    g.export_instances(updated)
    (DEST/'Rover_RevG_Assembly.step').rename(DEST/'Rover_RevI_Assembly.step')
    budgets=[
      dict(id='interface_board',role='Secured perfboard for level dividers, buzzer transistor and audio coupling',size_mm=[50,30,16],origin_mm=[24,-25,42]),
      dict(id='protection_board',role='Battery protection board selected within this allowance',size_mm=[42,18,12],origin_mm=[20,9,42]),
      dict(id='additional_regulator',role='Optional motor regulator selected after current tests, within this allowance',size_mm=[42,21,22],origin_mm=[64,6,42]),
      dict(id='inline_fuse',role='Insulated fuse holder within this allowance',size_mm=[26,13,13],origin_mm=[78,-25,42])]
    (DEST/'POWER_BAY_BUDGETS.json').write_text(json.dumps(dict(status='Allocated installation envelopes, not measured or electrically selected hardware',boards=budgets,board_seat_z_mm=42,tray_top_z_mm=38,insulating_standoff_budget_mm=4,onboard_charger='No onboard charger allocated. Use a correctly matched external charger after pack/cell verification; remove or isolate the pack as required by its charger.',mount='Four M3 x 12 screws, plain nuts and washers; new shell underside nut pockets. Boards use insulating 4 mm supports and narrow ties through adjustable tray slots. Keep clear of component bodies and conductors.'),indent=2)+'\n')
    (DEST/'verification/revH_baseline.json').write_text(json.dumps({p['id']:dict(bounds=p['bounds'],hash=hashlib.sha256((SOURCE/p['step']).read_bytes()).hexdigest()) for p in json.loads((SOURCE/'parts.json').read_text())},indent=2)+'\n')
    print(DEST,flush=True)
if __name__=='__main__':main()
