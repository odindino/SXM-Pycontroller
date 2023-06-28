import SXMRemote

MySXM= SXMRemote.DDEClient("SXM","Remote");
MySXM.GetIniEntry('Save','Path')
