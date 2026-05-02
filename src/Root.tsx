import { Composition } from "remotion";
import { InstagramReel } from "./InstagramReel";
import { DigitaleProducten } from "./DigitaleProducten";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="InstagramReel"
        component={InstagramReel}
        durationInFrames={600}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="DigitaleProducten"
        component={DigitaleProducten}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
