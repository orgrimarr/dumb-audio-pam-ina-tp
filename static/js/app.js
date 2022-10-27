const fetchAssets = async function () {
  const result = await fetch('/assets')
  if (result.status !== 200) {
    throw new Error(`Error fetching asset list. ${result.status} ${result.statusText} ${await result.text()}`)
  }
  const assets = await result.json()
  return (assets || [])
    .map(asset => {
      asset.date = asset.date
        ? new Date(asset.date)
        : new Date(Date.now())
      return asset
    })
    .sort((asset1, asset2) => {
      return asset1.date.getTime() < asset2.date.getTime()
    })
}

const fetchAssetMediaStatus = async function (assetID) {
  const result = await fetch(`assets/${assetID}/media_status`)
  if (result.status !== 200) {
    throw new Error(`Error fetching asset list. ${result.status} ${result.statusText} ${await result.text()}`)
  }
  const data = await result.json()
  return data
}

let audio = null
const loadPlayer = function (mediaURI) {
  console.log('loadPlayer', mediaURI)

  try {
    if (audio) {
      audio.pause()
    }
  }
  catch (e) { }
  document.querySelector('#player').style.display = 'none'

  if (!mediaURI) {
    return
  }

  // (A) AUDIO OBJECT + HTML CONTROLS
  audio = new Audio(mediaURI),
    aPlay = document.getElementById("aPlay"),
    aPlayIco = document.getElementById("aPlayIco"),
    aNow = document.getElementById("aNow"),
    aTime = document.getElementById("aTime"),
    aSeek = document.getElementById("aSeek"),
    aVolume = document.getElementById("aVolume"),
    aVolIco = document.getElementById("aVolIco");

  // (B) PLAY & PAUSE
  // (B1) CLICK TO PLAY/PAUSE
  aPlay.onclick = () => {
    if (audio.paused) { audio.play(); }
    else { audio.pause(); }
  };

  // (B2) SET PLAY/PAUSE ICON
  audio.onplay = () => { aPlayIco.innerHTML = "pause"; };
  audio.onpause = () => { aPlayIco.innerHTML = "play_arrow"; };

  // (C) TRACK PROGRESS & SEEK TIME
  // (C1) SUPPORT FUNCTION - FORMAT HH:MM:SS
  const timeString = (secs) => {
    // HOURS, MINUTES, SECONDS
    let ss = Math.floor(secs),
      hh = Math.floor(ss / 3600),
      mm = Math.floor((ss - (hh * 3600)) / 60);
    ss = ss - (hh * 3600) - (mm * 60);

    // RETURN FORMATTED TIME
    if (hh > 0) { mm = mm < 10 ? "0" + mm : mm; }
    ss = ss < 10 ? "0" + ss : ss;
    return hh > 0 ? `${hh}:${mm}:${ss}` : `${mm}:${ss}`;
  };

  // (C2) TRACK LOADING
  audio.onloadstart = () => {
    aNow.innerHTML = "Loading";
    aTime.innerHTML = "";
  };

  // (C3) ON META LOADED
  audio.onloadedmetadata = () => {
    // (C3-1) INIT SET TRACK TIME
    aNow.innerHTML = timeString(0);
    aTime.innerHTML = timeString(audio.duration);

    // (C3-2) SET SEEK BAR MAX TIME
    aSeek.max = Math.floor(audio.duration);

    // (C3-3) USER CHANGE SEEK BAR TIME
    const aSeeking = false; // user is now changing time
    aSeek.oninput = () => { aSeeking = true; }; // prevents clash with (c3-4)
    aSeek.onchange = () => {
      audio.currentTime = aSeek.value;
      if (!audio.paused) { audio.play(); }
      aSeeking = false;
    };

    // (C3-4) UPDATE SEEK BAR ON PLAYING
    audio.ontimeupdate = () => {
      if (!aSeeking) { aSeek.value = Math.floor(audio.currentTime); }
    };
  };

  // (C4) UPDATE TIME ON PLAYING
  audio.ontimeupdate = () => {
    aNow.innerHTML = timeString(audio.currentTime);
  };

  // (D) VOLUME
  aVolume.onchange = () => {
    audio.volume = aVolume.value;
    aVolIco.innerHTML = (aVolume.value == 0 ? "volume_mute" : "volume_up");
  };

  // (E) ENABLE/DISABLE CONTROLS
  audio.oncanplaythrough = () => {
    aPlay.disabled = false;
    aVolume.disabled = false;
    aSeek.disabled = false;
  };
  audio.onwaiting = () => {
    aPlay.disabled = true;
    aVolume.disabled = true;
    aSeek.disabled = true;
  };

  document.querySelector('#player').style.display = 'block'
}

const openAsset = async function (asset) {
  document.querySelector('#asset-detail-title').innerText = asset.title || 'Unknown title'

  document.querySelector('#asset-id').innerText = asset.id || ''
  document.querySelector('#asset-title').innerText = asset.title || 'Unknown title'
  document.querySelector('#asset-author').innerText = asset.author || 'Unknown author'
  document.querySelector('#asset-description').innerText = asset.body || ''

  const mediaStatus = await fetchAssetMediaStatus(asset.id)
  document.querySelector('#asset-media-status').innerText = mediaStatus?.status || 'Media not found'

  loadPlayer(mediaStatus?.uri)
}

const buildAssetDom = function (asset) {
  const template = document.querySelector('#asset')
  const assetContainer = template.content.cloneNode(true)

  assetContainer.querySelector('.asset-title').innerText = asset.title
  assetContainer.querySelector('.asset-author').innerText = asset.author

  assetContainer.querySelector('.asset-date').innerText = asset.date.toLocaleString()

  assetContainer.querySelectorAll('*').forEach(node => {
    let canOpen = true // dumb debouncce
    node.addEventListener('click', () => {
      if (!canOpen) {
        return
      }
      canOpen = false
      openAsset(asset)
        .then(() => {
          canOpen = true
        })
        .catch(error => {
          canOpen = true
          console.error(error)
          alert(`Error opening asset ${asset.id}. ${error.message}`)
        })
    })
  })

  return assetContainer
}

const displayAssets = function (assets) {
  const container = document.querySelector('#asset-list')
  container.innerHTML = ''
  for (const asset of assets) {
    const child = buildAssetDom(asset)
    container.appendChild(child)
  }
}

const init = async function () {
  let assets = await fetchAssets()
  displayAssets(assets)
}


document.addEventListener('DOMContentLoaded', () => {
  init()
    .catch(error => {
      console.error(error)
      alert(`Error loading app. ${error.message}`)
    })
})